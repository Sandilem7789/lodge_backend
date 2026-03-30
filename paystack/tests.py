import json
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings

from bookings.models import Booking
from paystack.models import Order
from paystack.utils import (
    rand_to_cents,
    cents_to_rand,
    validate_amount_not_in_cents,
    get_paystack_amount,
    get_display_amount,
)


class PaystackUtilsTests(TestCase):
    """Test Paystack amount conversion utilities."""
    
    def test_rand_to_cents_conversion(self):
        """Test converting ZAR (rand) to cents."""
        # 100 ZAR = 10,000 cents
        self.assertEqual(rand_to_cents(Decimal('100.00')), 10000)
        
        # 4000.50 ZAR = 400,050 cents
        self.assertEqual(rand_to_cents(Decimal('4000.50')), 400050)
        
        # 0.01 ZAR = 1 cent (minimum)
        self.assertEqual(rand_to_cents(Decimal('0.01')), 1)
    
    def test_cents_to_rand_conversion(self):
        """Test converting cents back to ZAR (rand)."""
        # 10,000 cents = 100 ZAR
        result = cents_to_rand(10000)
        self.assertEqual(result, Decimal('100.00'))
        
        # 400,050 cents = 4000.50 ZAR
        result = cents_to_rand(400050)
        self.assertEqual(result, Decimal('4000.50'))
        
        # 1 cent = 0.01 ZAR
        result = cents_to_rand(1)
        self.assertEqual(result, Decimal('0.01'))
    
    def test_round_trip_conversion(self):
        """Test that converting to cents and back preserves precision."""
        original = Decimal('1234.56')
        cents = rand_to_cents(original)
        back_to_rand = cents_to_rand(cents)
        self.assertEqual(back_to_rand, original)
    
    def test_validate_amount_not_in_cents(self):
        """Test validation to prevent double multiplication."""
        # Valid rand amounts should not raise
        validate_amount_not_in_cents(Decimal('100.00'))
        validate_amount_not_in_cents(Decimal('5000.50'))
        
        # Large amounts (100k+) trigger warning but don't raise
        validate_amount_not_in_cents(Decimal('150000.00'))
    
    def test_invalid_amount_format(self):
        """Test that invalid amount formats raise ValueError."""
        with self.assertRaises(ValueError):
            rand_to_cents('invalid')
        
        with self.assertRaises(ValueError):
            rand_to_cents(None)
        
        with self.assertRaises(ValueError):
            rand_to_cents(-100)
    
    def test_get_paystack_amount(self):
        """Test get_paystack_amount convenience function."""
        result = get_paystack_amount(Decimal('100.00'))
        self.assertEqual(result, 10000)
    
    def test_get_display_amount(self):
        """Test get_display_amount for frontend display."""
        result = get_display_amount(Decimal('100.00'))
        self.assertEqual(result, 100.00)
        self.assertIsInstance(result, float)


class PaystackInitializePaymentTests(TestCase):
    """Test the initialize_payment endpoint for Paystack transactions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.initialize_url = reverse('initialize_payment')
        
        # Create a test booking
        self.booking = Booking.objects.create(
            type='chalet',
            name='John Doe',
            email='john@example.com',
            phone='555-0100',
            check_in=date.today() + timedelta(days=7),
            check_out=date.today() + timedelta(days=10),
            guests=2,
            confirmation_number='TEST001'
        )
    
    @patch('paystack.views.requests.post')
    def test_initialize_with_booking_id(self, mock_post):
        """Test initializing payment with existing booking ID."""
        # Mock Paystack API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': True,
            'message': 'Authorization URL created',
            'data': {
                'authorization_url': 'https://checkout.paystack.com/test',
                'reference': 'TEST123ABC',
                'access_code': 'test_access',
            }
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        payload = {
            'booking_id': self.booking.id,
            'email': 'john@example.com',
        }
        
        response = self.client.post(
            self.initialize_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('authorization_url', data['data'])
        self.assertIn('reference', data['data'])
        self.assertEqual(data['data']['booking_id'], self.booking.id)
    
    @patch('paystack.views.requests.post')
    def test_initialize_with_amount_override(self, mock_post):
        """Test initializing payment with custom amount."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': True,
            'message': 'Authorization URL created',
            'data': {
                'authorization_url': 'https://checkout.paystack.com/test',
                'reference': 'TEST123ABC',
            }
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        payload = {
            'booking_id': self.booking.id,
            'email': 'john@example.com',
            'amount': '2400.00',  # Custom amount
        }
        
        response = self.client.post(
            self.initialize_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # Verify the amount was stored correctly
        order = Order.objects.get(booking=self.booking)
        self.assertEqual(order.amount, Decimal('2400.00'))
    
    @patch('paystack.views.requests.post')
    def test_initialize_without_booking_id_creates_booking(self, mock_post):
        """Test initializing payment with full booking details (creates new booking)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': True,
            'message': 'Authorization URL created',
            'data': {
                'authorization_url': 'https://checkout.paystack.com/test',
                'reference': 'TEST456DEF',
            }
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        payload = {
            'type': 'chalet',
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'phone': '555-0200',
            'check_in': (date.today() + timedelta(days=7)).isoformat(),
            'check_out': (date.today() + timedelta(days=9)).isoformat(),
            'guests': 1,
            'amount': '1600.00',
        }
        
        response = self.client.post(
            self.initialize_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify booking was created
        booking = Booking.objects.get(email='jane@example.com')
        self.assertEqual(booking.type, 'chalet')
        self.assertEqual(booking.name, 'Jane Smith')
    
    def test_initialize_missing_email(self):
        """Test that missing email returns 400 error."""
        payload = {
            'booking_id': self.booking.id,
        }
        
        response = self.client.post(
            self.initialize_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('email', data['error'].lower())
    
    def test_initialize_invalid_booking_id(self):
        """Test that invalid booking ID returns 404 error."""
        payload = {
            'booking_id': 99999,
            'email': 'john@example.com',
        }
        
        response = self.client.post(
            self.initialize_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data['success'])
    
    @patch('paystack.views.requests.post')
    def test_paystack_api_error_handling(self, mock_post):
        """Test handling of Paystack API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'status': False,
            'message': 'Invalid email address',
        }
        mock_post.return_value = mock_response
        
        payload = {
            'booking_id': self.booking.id,
            'email': 'invalid-email',
        }
        
        response = self.client.post(
            self.initialize_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    @patch('paystack.views.requests.post')
    def test_already_paid_booking_error(self, mock_post):
        """Test that attempting to pay an already-paid booking returns error."""
        # Create an order and mark it as paid
        order = Order.objects.create(
            booking=self.booking,
            amount=Decimal('2400.00'),
            currency='ZAR',
            email='john@example.com',
            reference='PAID123',
            status='paid'
        )
        
        payload = {
            'booking_id': self.booking.id,
            'email': 'john@example.com',
        }
        
        response = self.client.post(
            self.initialize_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('already paid', data['error'].lower())


class PaystackCallbackTests(TestCase):
    """Test the Paystack callback (verification after redirect)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.callback_url = reverse('paystack:callback')
        
        # Create a test booking and order
        self.booking = Booking.objects.create(
            type='chalet',
            name='John Doe',
            email='john@example.com',
            phone='555-0100',
            check_in=date.today() + timedelta(days=7),
            check_out=date.today() + timedelta(days=10),
            guests=2,
            confirmation_number='TEST001'
        )
        
        self.order = Order.objects.create(
            booking=self.booking,
            amount=Decimal('2400.00'),
            currency='ZAR',
            email='john@example.com',
            reference='TEST_REF_123',
            status='pending'
        )
    
    @patch('paystack.views.requests.get')
    def test_successful_payment_callback(self, mock_get):
        """Test successful payment verification via callback."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': True,
            'message': 'Authorization URL created',
            'data': {
                'reference': 'TEST_REF_123',
                'amount': 240000,  # in cents
                'status': 'success',
                'paid_at': '2024-02-05T10:30:00.000Z',
            }
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        response = self.client.get(
            self.callback_url,
            {'reference': 'TEST_REF_123'}
        )
        
        # Should redirect to booking confirmation
        self.assertIn(response.status_code, [301, 302])
        
        # Verify order status was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')
    
    @patch('paystack.views.requests.get')
    def test_failed_payment_callback(self, mock_get):
        """Test failed payment verification via callback."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': True,
            'data': {
                'reference': 'TEST_REF_123',
                'status': 'failed',
            }
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        response = self.client.get(
            self.callback_url,
            {'reference': 'TEST_REF_123'}
        )
        
        # Should redirect to payment failed
        self.assertIn(response.status_code, [301, 302])
        
        # Verify order status was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'failed')
    
    def test_callback_missing_reference(self):
        """Test callback without reference parameter."""
        response = self.client.get(self.callback_url)
        
        # Should redirect with error
        self.assertIn(response.status_code, [301, 302])
    
    @patch('paystack.views.requests.get')
    def test_callback_with_invalid_reference(self, mock_get):
        """Test callback with non-existent reference."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': False,
            'message': 'Reference not found',
        }
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        response = self.client.get(
            self.callback_url,
            {'reference': 'NONEXISTENT'}
        )
        
        # Should redirect with error
        self.assertIn(response.status_code, [301, 302])


class PaystackVerifyEndpointTests(TestCase):
    """Test the manual verify endpoint (POST /api/payments/verify/)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.verify_url = reverse('verify_payment')
        
        # Create a test booking and order
        self.booking = Booking.objects.create(
            type='chalet',
            name='John Doe',
            email='john@example.com',
            phone='555-0100',
            check_in=date.today() + timedelta(days=7),
            check_out=date.today() + timedelta(days=10),
            guests=2,
            confirmation_number='TEST001'
        )
        
        self.order = Order.objects.create(
            booking=self.booking,
            amount=Decimal('2400.00'),
            currency='ZAR',
            email='john@example.com',
            reference='TEST_REF_456',
            status='pending'
        )
    
    @patch('paystack.views.requests.get')
    def test_verify_successful_transaction(self, mock_get):
        """Test verifying a successful transaction."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': True,
            'message': 'Authorization URL created',
            'data': {
                'reference': 'TEST_REF_456',
                'amount': 240000,
                'status': 'success',
                'paid_at': '2024-02-05T10:30:00.000Z',
            }
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        payload = {'reference': 'TEST_REF_456'}
        
        response = self.client.post(
            self.verify_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify order and booking were updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')
        
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'confirmed')
    
    def test_verify_missing_reference(self):
        """Test verify endpoint without reference."""
        payload = {}
        
        response = self.client.post(
            self.verify_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    @patch('paystack.views.requests.get')
    def test_verify_nonexistent_order(self, mock_get):
        """Test verifying a reference that doesn't exist."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': False,
            'message': 'Reference not found',
        }
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Use a reference that doesn't exist in our DB
        payload = {'reference': 'NONEXISTENT_REF'}
        
        response = self.client.post(
            self.verify_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data['success'])


class PaymentMobileFlowTests(TestCase):
    """Test complete payment flow for mobile (server-initialized + redirect)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.initialize_url = reverse('initialize_payment')
        self.verify_url = reverse('verify_payment')
        
        self.booking = Booking.objects.create(
            type='chalet',
            name='Mobile User',
            email='mobile@example.com',
            phone='555-9999',
            check_in=date.today() + timedelta(days=5),
            check_out=date.today() + timedelta(days=7),
            guests=1,
            confirmation_number='MOB001'
        )
    
    @patch('paystack.views.requests.post')
    @patch('paystack.views.requests.get')
    def test_complete_mobile_payment_flow(self, mock_get, mock_post):
        """Test complete payment flow: initialize -> redirect -> verify."""
        # Step 1: Initialize payment
        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {
            'status': True,
            'message': 'Authorization URL created',
            'data': {
                'authorization_url': 'https://checkout.paystack.com/test123',
                'reference': 'MOB_PAY_123',
            }
        }
        mock_post_response.status_code = 200
        mock_post.return_value = mock_post_response
        
        init_payload = {
            'booking_id': self.booking.id,
            'email': 'mobile@example.com',
        }
        
        init_response = self.client.post(
            self.initialize_url,
            data=json.dumps(init_payload),
            content_type='application/json'
        )
        
        self.assertEqual(init_response.status_code, 201)
        init_data = init_response.json()
        self.assertTrue(init_data['success'])
        authorization_url = init_data['data']['authorization_url']
        reference = init_data['data']['reference']
        
        # Step 2: User is redirected to Paystack, completes payment, and is redirected back
        # (Paystack redirects to callback URL with reference parameter)
        
        # Step 3: Verify transaction
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            'status': True,
            'message': 'Authorization URL created',
            'data': {
                'reference': reference,
                'amount': 160000,  # 1600 ZAR in cents
                'status': 'success',
            }
        }
        mock_get_response.status_code = 200
        mock_get.return_value = mock_get_response
        
        verify_payload = {'reference': reference}
        
        verify_response = self.client.post(
            self.verify_url,
            data=json.dumps(verify_payload),
            content_type='application/json'
        )
        
        self.assertEqual(verify_response.status_code, 200)
        verify_data = verify_response.json()
        self.assertTrue(verify_data['success'])
        
        # Verify final state
        order = Order.objects.get(reference=reference)
        self.assertEqual(order.status, 'paid')
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'confirmed')
