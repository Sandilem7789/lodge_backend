import logging
from collections import OrderedDict
from decimal import Decimal
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bookings.models import Booking
from bookings.serializers import BookingSerializer
from .models import Order
from .serializers import OrderSerializer
from .utils import (
    generate_payfast_signature,
    validate_payfast_itn,
    validate_amount_not_in_cents,
    format_payfast_amount,
)

logger = logging.getLogger('payfast')

PAYFAST_ONSITE_URL_SANDBOX = 'https://sandbox.payfast.co.za/onsite/process'
PAYFAST_ONSITE_URL_LIVE = 'https://www.payfast.co.za/onsite/process'


def _get_payfast_onsite_url():
    if getattr(settings, 'PAYFAST_SANDBOX', True):
        return PAYFAST_ONSITE_URL_SANDBOX
    return PAYFAST_ONSITE_URL_LIVE


def _parse_request_data(request):
    """Parse JSON or form-encoded POST body."""
    import json
    try:
        if 'application/json' in request.content_type:
            return json.loads(request.body.decode('utf-8') or '{}')
        return request.POST.dict()
    except Exception:
        return {}


def _build_payfast_params(order, booking, email, return_url, cancel_url, notify_url):
    """
    Build the PayFast form parameters in the required field order.
    Returns an OrderedDict — the order matters for signature generation.
    """
    name_parts = (booking.name or 'Guest').strip().split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''

    amount_str = format_payfast_amount(order.amount)
    item_name = f"Ikhaya Lami Lodge - {booking.type.capitalize()} Booking"

    # In sandbox mode PayFast rejects when the buyer email matches the merchant account.
    # Use PayFast's dedicated sandbox buyer account to avoid this.
    sandbox = getattr(settings, 'PAYFAST_SANDBOX', True)
    buyer_email = 'sbtu01@payfast.co.za' if sandbox else email

    # Field order MUST match PayFast's expected order for correct signature generation
    params = OrderedDict([
        ('merchant_id', settings.PAYFAST_MERCHANT_ID),
        ('merchant_key', settings.PAYFAST_MERCHANT_KEY),
        ('return_url', return_url),
        ('cancel_url', cancel_url),
        ('notify_url', notify_url),
        ('m_payment_id', str(order.order_id)),
        ('amount', amount_str),
        ('item_name', item_name),
        ('email_address', buyer_email),
        ('name_first', first_name),
    ])

    if last_name:
        params['name_last'] = last_name

    passphrase = getattr(settings, 'PAYFAST_PASSPHRASE', '')
    signature = generate_payfast_signature(params, passphrase)
    params['signature'] = signature

    return params


# ---------------------------------------------------------------------------
# Main payment endpoints
# ---------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(['POST'])
def initialize_payment(request):
    """
    Initialize a PayFast payment for a booking.
    POST /api/payments/initialize/

    Accepts:
        { email, amount, booking_id, order_id, callback_url, cancel_url }
      OR full booking details (type, name, email, phone, ...)

    Returns:
        { success: true, data: { payfast_url, params, reference, booking_id } }
    """
    try:
        logger.debug(
            "initialize_payment: method=%s content_type=%s origin=%s",
            request.method, request.content_type, request.META.get('HTTP_ORIGIN'),
        )

        data = _parse_request_data(request)
        logger.debug("initialize_payment request data: %s", data)

        email = data.get('email')
        booking_id = data.get('booking_id')
        order_id = data.get('order_id')
        amount_override = data.get('amount')
        callback_url = data.get('callback_url') or data.get('return_url')
        cancel_url = data.get('cancel_url')

        # Derive frontend origin for default URLs
        origin = (
            request.META.get('HTTP_ORIGIN')
            or getattr(settings, 'FRONTEND_URL', '')
            or 'http://localhost:5173'
        )
        return_url = callback_url or f"{origin}/payment-callback/"
        cancel_url = cancel_url or f"{origin}/"
        notify_url = request.build_absolute_uri('/api/payments/notify/')

        booking = None
        order = None

        # --- Resolve booking ---
        if booking_id:
            try:
                booking = Booking.objects.get(id=booking_id)
            except Booking.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Booking not found'}, status=404)
        elif order_id:
            order = Order.objects.filter(order_id=order_id).first()
            if order:
                booking = order.booking
            else:
                return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)

        # --- Create booking from full details if not found ---
        if not booking:
            booking_keys = {'type', 'name', 'email', 'phone', 'check_in', 'check_out', 'guests'}
            if set(data.keys()) & booking_keys:
                serializer_input = {k: data[k] for k in booking_keys if data.get(k) is not None}
                if not all(serializer_input.get(k) for k in ('email', 'name', 'type')):
                    return JsonResponse(
                        {'success': False, 'error': 'Insufficient booking data (name, email, type required)'},
                        status=400,
                    )
                serializer = BookingSerializer(data=serializer_input)
                if serializer.is_valid():
                    booking = serializer.save()
                    email = email or booking.email
                else:
                    logger.error("Booking validation errors: %s", serializer.errors)
                    return JsonResponse(
                        {'success': False, 'error': 'Invalid booking data', 'errors': serializer.errors},
                        status=400,
                    )
            else:
                return JsonResponse(
                    {'success': False, 'error': 'booking_id, order_id, or full booking details are required'},
                    status=400,
                )

        if not email:
            return JsonResponse({'success': False, 'error': 'email is required'}, status=400)

        # --- Resolve or create order ---
        if not order:
            order = Order.objects.filter(booking=booking).first()

        if order and order.status == 'paid':
            return JsonResponse({'success': False, 'error': 'Booking already paid'}, status=400)

        # --- Determine amount ---
        if amount_override is not None:
            try:
                amount = Decimal(str(amount_override))
                validate_amount_not_in_cents(amount)
            except (ValueError, TypeError) as exc:
                return JsonResponse({'success': False, 'error': f'Invalid amount: {exc}'}, status=400)
        elif order and order.amount:
            amount = order.amount
        elif booking.amount:
            amount = booking.amount
        else:
            from bookings.pricing import calculate_booking_amount
            amount = calculate_booking_amount(booking.type, booking.check_in, booking.check_out)
            booking.amount = amount
            booking.save()

        # --- Create / update order ---
        if order:
            order.amount = amount
            order.email = email
            order.status = 'pending'
            order.save()
        else:
            order = Order.objects.create(
                booking=booking,
                amount=amount,
                currency='ZAR',
                email=email,
                status='pending',
            )

        # Use order_id as our stable reference (m_payment_id for PayFast)
        reference = str(order.order_id)
        order.reference = reference
        order.save()

        # --- Build PayFast params and return to frontend for form redirect ---
        params = _build_payfast_params(order, booking, email, return_url, cancel_url, notify_url)
        sandbox = getattr(settings, 'PAYFAST_SANDBOX', True)
        payfast_url = (
            'https://sandbox.payfast.co.za/eng/process'
            if sandbox else
            'https://www.payfast.co.za/eng/process'
        )

        logger.info(
            "PayFast redirect: reference=%s amount=%s booking=%s url=%s",
            reference, amount, booking.id, payfast_url,
        )
        logger.debug("PayFast params: %s", dict(params))

        return JsonResponse({
            'success': True,
            'data': {
                'payfast_url': payfast_url,
                'params': dict(params),
                'reference': reference,
                'booking_id': booking.id,
            },
        }, status=201)

    except Exception as exc:
        logger.exception("Error in initialize_payment: %s", exc)
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(['POST'])
def verify_payment(request):
    """
    Verify payment status for a given reference (m_payment_id).
    POST /api/payments/verify/

    Accepts: { "reference": "<m_payment_id>" }
    Returns booking confirmation details if payment is marked as paid.
    """
    try:
        data = _parse_request_data(request)
        logger.debug("verify_payment request data: %s", data)

        reference = data.get('reference')
        if not reference:
            return JsonResponse({'success': False, 'error': 'reference is required'}, status=400)

        order = Order.objects.filter(reference=reference).first()
        if not order:
            return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)

        # If ITN hasn't arrived yet (e.g. localhost dev) but PayFast return URL
        # confirms COMPLETE, trust it and mark the order paid now.
        payment_status = data.get('payment_status', '').upper()
        if order.status != 'paid' and payment_status == 'COMPLETE':
            order.status = 'paid'
            order.save()
            booking = order.booking
            booking.status = 'confirmed'
            booking.save()
            logger.info(
                "Order %s marked paid via return-URL payment_status (ITN not yet received)",
                reference,
            )

        if order.status == 'paid':
            booking = order.booking
            return JsonResponse({
                'success': True,
                'data': {
                    'reference': reference,
                    'confirmation_number': booking.confirmation_number,
                    'booking_id': str(booking.id),
                    'amount': float(order.amount),
                    'email': order.email,
                    'booking': {
                        'name': booking.name,
                        'type': booking.type,
                        'check_in': booking.check_in.isoformat() if booking.check_in else None,
                        'check_out': booking.check_out.isoformat() if booking.check_out else None,
                        'guests': booking.guests,
                    },
                },
            }, status=200)

        # Payment not yet confirmed
        return JsonResponse({
            'success': False,
            'error': 'Payment not yet verified',
            'status': order.status,
        }, status=400)

    except Exception as exc:
        logger.exception("Error in verify_payment: %s", exc)
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(['POST'])
def itn_notification(request):
    """
    PayFast Instant Transaction Notification (ITN) handler.
    POST /api/payments/notify/

    PayFast POSTs form data here server-to-server after every transaction.
    We validate the signature and update the order status.
    """
    try:
        post_data = request.POST.dict()
        logger.info("PayFast ITN received: %s", post_data)

        passphrase = getattr(settings, 'PAYFAST_PASSPHRASE', '')
        if not validate_payfast_itn(post_data, passphrase):
            logger.error(
                "PayFast ITN signature validation failed. received=%s",
                post_data.get('signature'),
            )
            return HttpResponse('Invalid signature', status=400)

        m_payment_id = post_data.get('m_payment_id')
        payment_status = post_data.get('payment_status', '').upper()

        if not m_payment_id:
            logger.warning("ITN missing m_payment_id")
            return HttpResponse('Missing m_payment_id', status=400)

        order = Order.objects.filter(reference=m_payment_id).first()
        if not order:
            logger.warning("ITN: order not found for reference=%s", m_payment_id)
            return HttpResponse('Order not found', status=404)

        if payment_status == 'COMPLETE':
            order.status = 'paid'
            order.save()
            booking = order.booking
            booking.status = 'confirmed'
            booking.save()
            logger.info(
                "PayFast payment complete: order=%s booking=%s",
                m_payment_id, booking.id,
            )
        elif payment_status in ('FAILED', 'CANCELLED'):
            order.status = 'failed'
            order.save()
            logger.warning("PayFast payment %s: order=%s", payment_status, m_payment_id)
        else:
            logger.info("PayFast ITN status=%s order=%s (no action)", payment_status, m_payment_id)

        return HttpResponse('OK', status=200)

    except Exception as exc:
        logger.exception("Error in itn_notification: %s", exc)
        return HttpResponse('Internal server error', status=500)


# ---------------------------------------------------------------------------
# Order list (staff)
# ---------------------------------------------------------------------------

class OrderListView(APIView):
    """List orders — staff only. GET /api/payfast/orders/"""

    def get(self, request):
        try:
            orders = Order.objects.all()
            status_filter = request.query_params.get('status')
            if status_filter:
                orders = orders.filter(status=status_filter)
            booking_id = request.query_params.get('booking_id')
            if booking_id:
                orders = orders.filter(booking_id=booking_id)
            serializer = OrderSerializer(orders, many=True)
            return Response({'count': orders.count(), 'data': serializer.data}, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("Error in OrderListView: %s", exc)
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
