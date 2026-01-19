import requests
import logging
from decimal import Decimal
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bookings.models import Booking
from bookings.serializers import BookingSerializer
from .models import Order
from .serializers import OrderSerializer
from .utils import rand_to_cents, get_paystack_amount, get_display_amount, validate_amount_not_in_cents

logger = logging.getLogger('paystack')

# Paystack API endpoints
PAYSTACK_INITIALIZE_URL = 'https://api.paystack.co/transaction/initialize'
PAYSTACK_VERIFY_URL = 'https://api.paystack.co/transaction/verify'


class InitializePaymentView(APIView):
    """
    Initialize a Paystack payment for a booking.
    POST /api/paystack/initialize-payment/
    
    Payload:
    {
        "booking_id": 123,
        "email": "customer@example.com",
        "callback_url": "https://yourdomain.com/payment-callback/"
    }
    """
    
    def post(self, request):
        """Initialize Paystack transaction."""
        try:
            booking_id = request.data.get('booking_id')
            email = request.data.get('email')
            callback_url = request.data.get('callback_url')
            
            # Validate inputs
            if not all([booking_id, email, callback_url]):
                return Response(
                    {'message': 'Missing required fields: booking_id, email, callback_url'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get booking
            try:
                booking = Booking.objects.get(id=booking_id)
            except Booking.DoesNotExist:
                return Response(
                    {'message': 'Booking not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if order already exists for this booking
            existing_order = Order.objects.filter(booking=booking).first()
            if existing_order and existing_order.status == 'paid':
                return Response(
                    {'message': 'Booking already paid'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate amount based on booking type and duration
            amount = self._calculate_amount(booking)
            
            # Create order record
            if existing_order:
                order = existing_order
                order.amount = amount
                order.email = email
                order.status = 'pending'
            else:
                order = Order.objects.create(
                    booking=booking,
                    amount=amount,
                    currency=settings.PAYSTACK_CURRENCY,
                    email=email,
                    status='pending'
                )
            # Ensure a stable reference is set and stored on the order
            reference = str(order.order_id)
            order.reference = reference
            order.save()

            # Prepare Paystack payload (use customer's email from form)
            # Convert amount from ZAR (rand) to cents for Paystack
            amount_cents = get_paystack_amount(amount)
            
            paystack_payload = {
                'email': email,
                'amount': amount_cents,  # Amount in cents for Paystack
                'currency': settings.PAYSTACK_CURRENCY,
                'reference': reference,
                'callback_url': callback_url,
                'metadata': {
                    'booking_id': booking.id,
                    'booking_type': booking.type,
                    'guests': booking.guests,
                    'confirmation_number': booking.confirmation_number,
                }
            }
            
            logger.info(f"Initializing Paystack payment for order {order.order_id}")
            logger.debug(f"Customer email: {email}")
            logger.debug(f"Paystack payload: {paystack_payload}")
            
            # Call Paystack API
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                PAYSTACK_INITIALIZE_URL,
                json=paystack_payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            paystack_response = response.json()
            logger.info(f"Paystack initialize response: {paystack_response}")

            if paystack_response.get('status'):
                # store/refine reference from Paystack (normally same as provided)
                order.reference = paystack_response['data'].get('reference', reference)
                order.save()

                return Response({
                    'message': 'Payment initialized successfully',
                    'data': {
                        'order_id': order.order_id,
                        'amount': get_display_amount(order.amount),  # Return amount in rand
                        'currency': order.currency,
                        'authorization_url': paystack_response['data']['authorization_url'],
                        'reference': order.reference,
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                error_msg = paystack_response.get('message', 'Payment initialization failed')
                logger.error(f"Paystack error: {error_msg}")
                return Response(
                    {'message': f'Payment initialization failed: {error_msg}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except requests.RequestException as e:
            logger.error(f"Paystack API error: {str(e)}")
            return Response(
                {'message': 'Payment service error. Please try again.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Unexpected error in initialize_payment: {str(e)}")
            return Response(
                {'message': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _calculate_amount(self, booking):
        """Calculate booking amount based on type and duration."""
        # Pricing per night/unit (customize based on your rates)
        pricing = {
            'chalet': Decimal('800.00'),
            'campsite': Decimal('200.00'),
            'conference': Decimal('5000.00'),
            'safari': Decimal('2500.00'),
            'event': Decimal('1000.00'),
        }
        
        base_price = pricing.get(booking.type, Decimal('500.00'))
        
        # For safari, use check_in only; others use stay duration
        if booking.type == 'safari':
            return base_price
        else:
            duration = (booking.check_out - booking.check_in).days
            return base_price * max(duration, 1)


class PaystackCallbackView(View):
    """
    Paystack callback view - called after user completes payment.
    GET /api/paystack/callback/?reference=<paystack_reference>
    """
    
    def get(self, request):
        """Verify Paystack transaction and update order status."""
        try:
            reference = request.GET.get('reference')
            
            if not reference:
                logger.warning('Paystack callback missing reference parameter')
                return redirect('/payment-failed/?message=Missing%20reference')
            
            logger.info(f"Processing Paystack callback for reference: {reference}")
            
            # Find order by reference
            order = Order.objects.filter(reference=reference).first()
            if not order:
                logger.warning(f"Order not found for reference: {reference}")
                return redirect('/payment-failed/?message=Order%20not%20found')
            
            # Verify transaction with Paystack
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            }
            
            verify_url = f'{PAYSTACK_VERIFY_URL}/{reference}'
            response = requests.get(
                verify_url,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            paystack_response = response.json()
            logger.info(f"Paystack verify response: {paystack_response}")
            
            if paystack_response.get('status'):
                transaction = paystack_response.get('data', {})
                
                if transaction.get('status') == 'success':
                    # Payment successful
                    order.status = 'paid'
                    order.save()
                    logger.info(f"Order {order.order_id} marked as paid")

                    # Redirect to booking confirmation page (frontend route)
                    try:
                        url = reverse('paystack:booking-confirmation', args=[order.order_id])
                    except Exception:
                        url = f'/api/paystack/booking-confirmation/{order.order_id}/'
                    return redirect(url)
                else:
                    # Payment failed
                    order.status = 'failed'
                    order.save()
                    logger.warning(f"Payment failed for order {order.order_id}")
                    return redirect(f'/payment-failed/?reference={reference}')
            else:
                # Verification failed
                error_msg = paystack_response.get('message', 'Verification failed')
                logger.error(f"Paystack verification error: {error_msg}")
                return redirect(f'/payment-failed/?message={error_msg}')
        
        except requests.RequestException as e:
            logger.error(f"Paystack verification API error: {str(e)}")
            return redirect('/payment-failed/?message=Service%20error')
        except Exception as e:
            logger.error(f"Unexpected error in paystack_callback: {str(e)}")
            return redirect('/payment-failed/?message=Unexpected%20error')


@method_decorator(require_http_methods(['GET']), name='dispatch')
class PaymentConfirmationView(View):
    """
    Display payment confirmation page.
    GET /api/paystack/confirmation/<order_id>/
    """
    
    def get(self, request, order_id):
        """Return payment confirmation details."""
        try:
            order = Order.objects.get(order_id=order_id)
            serializer = OrderSerializer(order)
            
            return JsonResponse({
                'message': 'Payment confirmed',
                'data': serializer.data,
                'booking': {
                    'confirmation_number': order.booking.confirmation_number,
                    'type': order.booking.type,
                    'check_in': order.booking.check_in,
                    'check_out': order.booking.check_out,
                    'guests': order.booking.guests,
                }
            }, status=200)
        except Order.DoesNotExist:
            return JsonResponse(
                {'message': 'Order not found'},
                status=404
            )
        except Exception as e:
            logger.error(f"Error in payment_confirmation: {str(e)}")
            return JsonResponse(
                {'message': 'An error occurred'},
                status=500
            )


@require_http_methods(['GET'])
def booking_confirmation(request, order_id):
    """Render booking confirmation page only when payment is verified (paid)."""
    try:
        order = Order.objects.get(order_id=order_id)

        if order.status != 'paid':
            logger.warning(f"Attempt to view confirmation for unpaid order {order.order_id}")
            context = {'error': 'Payment not completed for this booking.'}
            return render(request, 'paystack/booking_confirmation.html', context)

        # Payment is paid — show booking details
        context = {
            'order': order,
            'booking': order.booking,
        }
        return render(request, 'paystack/booking_confirmation.html', context)
    except Order.DoesNotExist:
        return render(request, 'paystack/booking_confirmation.html', {'error': 'Order not found.'})
    except Exception as e:
        logger.error(f"Error rendering booking confirmation: {str(e)}")
        return render(request, 'paystack/booking_confirmation.html', {'error': 'An unexpected error occurred.'})


class OrderListView(APIView):
    """
    List orders (staff-only endpoint).
    GET /api/paystack/orders/
    """
    
    def get(self, request):
        """List all orders with optional filters."""
        try:
            orders = Order.objects.all()
            
            # Optional filters
            status_filter = request.query_params.get('status')
            if status_filter:
                orders = orders.filter(status=status_filter)
            
            booking_id = request.query_params.get('booking_id')
            if booking_id:
                orders = orders.filter(booking_id=booking_id)
            
            serializer = OrderSerializer(orders, many=True)
            return Response({
                'message': 'Orders retrieved successfully',
                'count': orders.count(),
                'data': serializer.data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in order_list: {str(e)}")
            return Response(
                {'message': 'An error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


def _parse_request_data(request):
    """Helper to parse JSON or form data for POST requests."""
    data = {}
    try:
        if request.content_type == 'application/json':
            import json
            data = json.loads(request.body.decode('utf-8') or '{}')
        else:
            # form-encoded or multipart
            data = request.POST.dict()
    except Exception:
        data = {}
    return data


@csrf_exempt
@require_http_methods(['POST'])
def verify_payment(request):
    """
    Verify Paystack payment reference and update booking status.
    POST /api/payments/verify/
    
    Expects: { "reference": "paystack_reference" }
    Returns: { "success": true, "booking_id": ..., "status": "paid" } or { "success": false, "error": "..." }
    """
    try:
        data = _parse_request_data(request)
        logger.debug(f"Incoming verify_payment request data: {data}")
        
        reference = data.get('reference')
        if not reference:
            return JsonResponse({'success': False, 'error': 'reference is required'}, status=400)
        
        # Find order by reference
        order = Order.objects.filter(reference=reference).first()
        if not order:
            return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
        
        # Verify transaction with Paystack
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        }
        
        verify_url = f'{PAYSTACK_VERIFY_URL}/{reference}'
        response = requests.get(
            verify_url,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        paystack_response = response.json()
        logger.info(f"Paystack verify response: {paystack_response}")
        
        if paystack_response.get('status'):
            transaction = paystack_response.get('data', {})
            
            if transaction.get('status') == 'success':
                # Payment successful
                order.status = 'paid'
                order.save()
                
                # Update booking status to confirmed
                booking = order.booking
                booking.status = 'confirmed'
                booking.save()
                
                logger.info(f"Order {order.order_id} marked as paid, booking {booking.id} confirmed")
                
                return JsonResponse({
                    'success': True,
                    'data': {
                        'booking_id': booking.id,
                        'order_id': str(order.order_id),
                        'status': 'paid',
                        'reference': reference,
                    }
                }, status=200)
            else:
                # Payment failed
                order.status = 'failed'
                order.save()
                logger.warning(f"Payment failed for order {order.order_id}")
                return JsonResponse({
                    'success': False,
                    'error': 'Payment verification failed',
                    'status': 'failed',
                }, status=400)
        else:
            # Verification failed
            error_msg = paystack_response.get('message', 'Verification failed')
            logger.error(f"Paystack verification error: {error_msg}")
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
    
    except requests.RequestException as e:
        logger.error(f"Paystack verification API error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Payment service error'}, status=503)
    except Exception as e:
        logger.error(f"Unexpected error in verify_payment: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(['POST'])
def initialize_payment(request):
    """Function-based view to match frontend route `/api/payments/initialize/`.

    Accepts either:
    1. { email, amount, booking_id, order_id } - to initialize payment for existing booking
    2. Full booking details (type, name, email, etc.) - to create booking and initialize payment
    
    Returns JSON with Paystack `authorization_url`, `reference`, and `booking_id`.
    """
    try:
        # log basic request info for debugging (method, content type, origin)
        logger.debug(f"initialize_payment called: method={request.method}, content_type={request.content_type}, origin={request.META.get('HTTP_ORIGIN')}")
        logger.debug(f"Request headers: { {k: v for k, v in request.META.items() if k.startswith('HTTP_') or k in ['CONTENT_TYPE','CONTENT_LENGTH']} }")

        data = _parse_request_data(request)
        logger.debug(f"Incoming initialize_payment request data: {data}")

        email = data.get('email')
        booking_id = data.get('booking_id')
        order_id = data.get('order_id')
        amount_override = data.get('amount')  # Amount from request (required if provided)
        callback_url = data.get('callback_url') or request.build_absolute_uri('/api/paystack/callback/')

        booking = None
        order = None
        
        # Case 1: Check if booking_id or order_id is provided (existing booking)
        if booking_id:
            try:
                booking = Booking.objects.get(id=booking_id)
            except Booking.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
        elif order_id:
            order = Order.objects.filter(order_id=order_id).first()
            if order:
                booking = order.booking
            else:
                return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
        
        # Case 2: If no booking_id/order_id, check if full booking details are provided
        if not booking:
            booking_data_keys = {'type', 'name', 'email', 'phone', 'check_in', 'check_out', 'guests', 'safari_slot', 'message'}
            provided_keys = set(k for k in data.keys())
            if provided_keys & booking_data_keys:
                # Build serializer input from available fields
                serializer_input = {k: data.get(k) for k in booking_data_keys if data.get(k) is not None}
                # Ensure email/name/type present
                if not serializer_input.get('email') or not serializer_input.get('name') or not serializer_input.get('type'):
                    return JsonResponse({'success': False, 'error': 'Insufficient booking data (name, email, type required)'}, status=400)
                serializer = BookingSerializer(data=serializer_input)
                if serializer.is_valid():
                    booking = serializer.save()
                    # Use email from booking if not provided separately
                    if not email:
                        email = booking.email
                else:
                    logger.error(f"Booking validation errors: {serializer.errors}")
                    return JsonResponse({'success': False, 'error': 'Invalid booking data', 'errors': serializer.errors}, status=400)
            else:
                return JsonResponse({'success': False, 'error': 'Either booking_id/order_id or full booking details are required'}, status=400)

        # Validate email is present
        if not email:
            return JsonResponse({'success': False, 'error': 'email is required'}, status=400)

        # Check for existing paid order
        if not order:
            order = Order.objects.filter(booking=booking).first()
        
        if order and order.status == 'paid':
            return JsonResponse({'success': False, 'error': 'Booking already paid'}, status=400)

        # Use amount from request if provided, otherwise calculate from booking
        if amount_override is not None:
            try:
                amount = Decimal(str(amount_override))
                # Validate amount is in rand, not cents (prevent double multiplication)
                validate_amount_not_in_cents(amount)
            except ValueError as e:
                return JsonResponse({'success': False, 'error': f'Invalid amount: {str(e)}'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Invalid amount format'}, status=400)
        else:
            # Calculate from booking (use stored amount or calculate)
            if booking.amount:
                amount = booking.amount
            else:
                from bookings.pricing import calculate_booking_amount
                amount = calculate_booking_amount(booking.type, booking.check_in, booking.check_out)
                booking.amount = amount
                booking.save()

        # Create or update order
        if order:
            order.amount = amount
            order.email = email
            order.status = 'pending'
            order.save()
        else:
            order = Order.objects.create(
                booking=booking,
                amount=amount,
                currency=settings.PAYSTACK_CURRENCY,
                email=email,
                status='pending'
            )

        # Ensure reference stored
        reference = str(order.order_id)
        order.reference = reference
        order.save()

        # Build payload
        paystack_payload = {
            'email': email,
            'amount': get_paystack_amount(amount),  # Convert ZAR to cents for Paystack
            'currency': settings.PAYSTACK_CURRENCY,
            'reference': reference,
            'callback_url': callback_url,
            'metadata': {'booking_id': booking.id},
        }

        logger.debug(f"initialize_payment payload: {paystack_payload}")

        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }

        response = requests.post(PAYSTACK_INITIALIZE_URL, json=paystack_payload, headers=headers, timeout=10)
        logger.debug("Paystack raw response: %s %s", response.status_code, response.text)

        try:
            paystack_response = response.json()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON from Paystack', 'raw': response.text}, status=response.status_code)

        if response.status_code == 200 and paystack_response.get('status'):
            order.reference = paystack_response['data'].get('reference', reference)
            order.save()
            return JsonResponse({
                'success': True,
                'data': {
                    'authorization_url': paystack_response['data']['authorization_url'],
                    'reference': order.reference,
                    'booking_id': booking.id,
                }
            }, status=201)
        else:
            error_msg = paystack_response.get('message') or paystack_response.get('error') or 'Initialization failed'
            logger.error("Paystack init error: %s", error_msg)
            return JsonResponse({'success': False, 'error': error_msg, 'paystack_response': paystack_response}, status=response.status_code)

    except requests.RequestException as e:
        logger.error(f"Paystack API error: {e}")
        return JsonResponse({'success': False, 'error': 'Payment service error'}, status=503)
    except Exception as e:
        logger.error(f"Error in initialize_payment: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)
