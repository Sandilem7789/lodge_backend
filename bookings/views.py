from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.db.models import Q
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from decimal import Decimal

from .models import Booking
from .serializers import BookingSerializer, AvailabilitySerializer
from .pricing import calculate_booking_amount
from paystack.utils import validate_amount_not_in_cents
from datetime import timedelta, date


class BookingCreateView(APIView):
    """
    Handle POST requests to create new bookings.
    Endpoint: POST /api/bookings/
    """

    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            booking = serializer.save()
            
            # Calculate amount using seasonal pricing
            amount = calculate_booking_amount(
                booking.type,
                booking.check_in,
                booking.check_out
            )
            
            # Validate amount is in rand, not cents (prevent double multiplication)
            try:
                validate_amount_not_in_cents(amount)
            except ValueError as e:
                return Response(
                    {
                        'success': False,
                        'error': f'Invalid amount: {str(e)}',
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Store amount in booking
            booking.amount = amount
            booking.save()
            
            # Get or create order for this booking
            from paystack.models import Order
            from django.conf import settings
            
            order, created = Order.objects.get_or_create(
                booking=booking,
                defaults={
                    'amount': amount,
                    'currency': settings.PAYSTACK_CURRENCY,
                    'email': booking.email,
                    'status': 'pending'
                }
            )
            # Update amount if order already existed
            if not created:
                order.amount = amount
                order.email = booking.email
                order.save()
            
            # Return id, order_id, email, amount, confirmation_number
            return Response(
                {
                    'success': True,
                    'data': {
                        'id': booking.id,
                        'order_id': str(order.order_id),
                        'email': booking.email,
                        'amount': float(amount),
                        'confirmation_number': booking.confirmation_number,
                    }
                },
                status=status.HTTP_201_CREATED,
            )
        # Format errors for frontend
        error_message = 'Failed to create booking.'
        if serializer.errors:
            # Get first error message
            first_error = list(serializer.errors.values())[0]
            if isinstance(first_error, list) and len(first_error) > 0:
                error_message = first_error[0]
            elif isinstance(first_error, dict):
                first_nested = list(first_error.values())[0]
                if isinstance(first_nested, list) and len(first_nested) > 0:
                    error_message = first_nested[0]
        
        return Response(
            {
                'success': False,
                'error': error_message,
                'errors': serializer.errors,
                'details': serializer.errors,  # Frontend expects 'details'
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class AvailabilityCheckView(APIView):
    """
    Check availability for chalets, campsites, or conference venues.
    Endpoint: GET /api/bookings/availability/?type=chalet&check_in=2025-12-20&check_out=2025-12-25
    """

    def get(self, request):
        # Extract query parameters
        booking_type = request.query_params.get('type')
        check_in = request.query_params.get('check_in')
        check_out = request.query_params.get('check_out')

        # Validate input
        if not all([booking_type, check_in, check_out]):
            return Response(
                {
                    'message': 'Missing required parameters.',
                    'required': ['type', 'check_in', 'check_out'],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Use serializer for validation
        data = {
            'type': booking_type,
            'check_in': check_in,
            'check_out': check_out,
        }
        serializer = AvailabilitySerializer(data=data)

        if not serializer.is_valid():
            return Response(
                {
                    'message': 'Invalid query parameters.',
                    'errors': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for overlapping bookings of the same type
        overlapping_bookings = Booking.objects.filter(
            type=booking_type,
            check_in__lt=check_out,
            check_out__gt=check_in,
        )

        is_available = not overlapping_bookings.exists()

        return Response(
            {
                'type': booking_type,
                'check_in': check_in,
                'check_out': check_out,
                'available': is_available,
                'conflicting_bookings_count': overlapping_bookings.count(),
            },
            status=status.HTTP_200_OK,
        )


class BookingDetailView(APIView):
    """
    Retrieve a booking by confirmation number.
    Endpoint: GET /api/bookings/<confirmationNumber>/
    """

    def get(self, request, confirmation_number):
        try:
            booking = Booking.objects.get(confirmation_number=confirmation_number)
        except Booking.DoesNotExist:
            return Response(
                {'message': 'Booking not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BookingSerializer(booking)
        return Response(
            {
                'message': 'Booking retrieved successfully.',
                'data': serializer.data,
            },
            status=status.HTTP_200_OK,
        )
    
    def delete(self, request, confirmation_number):
        try:
            booking = Booking.objects.get(confirmation_number=confirmation_number)
        except Booking.DoesNotExist:
            return Response(
                {'message': 'Booking not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        booking.delete()
        return Response(
            {'message': 'Booking deleted successfully.'},
            status=status.HTTP_200_OK,
        )


class BookingListView(generics.ListAPIView):
    """
    List all bookings.
    Endpoint: GET /api/bookings/
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


class BookingListCreateView(APIView):
    """
    Handle both GET and POST requests on root endpoint.
    GET: List all bookings
    POST: Create a new booking
    Endpoint: GET/POST /api/bookings/
    """

    def get(self, request):
        """List all bookings with optional filters and search.

        Supported query params:
        - start_date (YYYY-MM-DD)
        - end_date (YYYY-MM-DD)
        - status
        - name (partial match on guest name)
        - search (searches name, email, confirmation_number)
        """
        bookings = Booking.objects.all()

        # Date range filtering
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            bookings = bookings.filter(check_in__gte=start_date)
        if end_date:
            bookings = bookings.filter(check_out__lte=end_date)

        # Status filter
        status_q = request.query_params.get('status')
        if status_q:
            bookings = bookings.filter(status__iexact=status_q)

        # Guest name filter
        name = request.query_params.get('name')
        if name:
            bookings = bookings.filter(name__icontains=name)

        # Search across name, email, confirmation_number
        search = request.query_params.get('search')
        if search:
            bookings = bookings.filter(
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(confirmation_number__icontains=search)
            )

        serializer = BookingSerializer(bookings, many=True)
        return Response(
            {
                'success': True,
                'data': {
                    'count': bookings.count(),
                    'items': serializer.data,
                },
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create a new booking."""
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            booking = serializer.save()
            
            # Calculate amount using seasonal pricing
            amount = calculate_booking_amount(
                booking.type,
                booking.check_in,
                booking.check_out
            )
            
            # Store amount in booking
            booking.amount = amount
            booking.save()
            
            # Get or create order for this booking
            from paystack.models import Order
            from django.conf import settings
            
            order, created = Order.objects.get_or_create(
                booking=booking,
                defaults={
                    'amount': amount,
                    'currency': settings.PAYSTACK_CURRENCY,
                    'email': booking.email,
                    'status': 'pending'
                }
            )
            # Update amount if order already existed
            if not created:
                order.amount = amount
                order.email = booking.email
                order.save()
            
            # Return id, order_id, email, amount, confirmation_number
            return Response(
                {
                    'success': True,
                    'data': {
                        'id': booking.id,
                        'order_id': str(order.order_id),
                        'email': booking.email,
                        'amount': float(amount),
                        'confirmation_number': booking.confirmation_number,
                    }
                },
                status=status.HTTP_201_CREATED,
            )
        # Format errors for frontend
        error_message = 'Failed to create booking.'
        if serializer.errors:
            # Get first error message
            first_error = list(serializer.errors.values())[0]
            if isinstance(first_error, list) and len(first_error) > 0:
                error_message = first_error[0]
            elif isinstance(first_error, dict):
                first_nested = list(first_error.values())[0]
                if isinstance(first_nested, list) and len(first_nested) > 0:
                    error_message = first_nested[0]
        
        return Response(
            {
                'success': False,
                'error': error_message,
                'errors': serializer.errors,
                'details': serializer.errors,  # Frontend expects 'details'
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class BookingCancelView(APIView):
    """
    Cancel a booking by marking its status as 'cancelled'.
    Endpoint: PATCH /api/bookings/<confirmation_number>/cancel/
    """

    def patch(self, request, confirmation_number):
        try:
            booking = Booking.objects.get(confirmation_number=confirmation_number)
        except Booking.DoesNotExist:
            return Response(
                {'message': 'Booking not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Accept optional cancellation_reason in PATCH body
        reason = request.data.get('cancellation_reason')
        booking.status = 'cancelled'
        booking.cancellation_reason = reason or booking.cancellation_reason
        booking.cancelled_at = timezone.now()
        booking.save()

        serializer = BookingSerializer(booking)
        return Response(
            {
                'message': 'Booking cancelled successfully.',
                'data': serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class GroupedBookingsView(APIView):
    """
    Return grouped booking counts by type and optional lists.
    Endpoint: GET /api/bookings/grouped/?type=chalet&start_date=&end_date=&status=&search=
    """

    def get(self, request):
        bookings = Booking.objects.all()

        # Apply same filters as listing
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            bookings = bookings.filter(check_in__gte=start_date)
        if end_date:
            bookings = bookings.filter(check_out__lte=end_date)

        status_q = request.query_params.get('status')
        if status_q:
            bookings = bookings.filter(status__iexact=status_q)

        search = request.query_params.get('search')
        if search:
            bookings = bookings.filter(
                Q(name__icontains=search) | Q(email__icontains=search) | Q(confirmation_number__icontains=search)
            )

        # If a specific type is requested, return list for that type
        req_type = request.query_params.get('type')
        result = {}
        types = [t[0] for t in Booking.BOOKING_TYPES]

        if req_type:
            filtered = bookings.filter(type=req_type)
            serializer = BookingSerializer(filtered, many=True)
            result = {
                'type': req_type,
                'count': filtered.count(),
                'data': serializer.data,
            }
            return Response(result, status=status.HTTP_200_OK)

        # Otherwise return counts per type
        for t in types:
            result[t] = bookings.filter(type=t).count()

        result['total'] = bookings.count()
        return Response(result, status=status.HTTP_200_OK)


class AvailabilityCalendarView(APIView):
    """
    Return fully booked dates per booking category.
    Endpoint: GET /api/availability/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    If no dates provided, defaults to next 30 days.
    """

    def get(self, request):
        # Date window
        start = request.query_params.get('start_date')
        end = request.query_params.get('end_date')
        today = timezone.now().date()
        if start:
            start_date = date.fromisoformat(start)
        else:
            start_date = today
        if end:
            end_date = date.fromisoformat(end)
        else:
            end_date = start_date + timedelta(days=30)

        # capacity definition must match serializer
        capacity = {
            'chalet': {'units': 3},
            'campsite': {'units': 10},
            'conference': {'units': 1},
            'safari': {'units': 3},
            'event': {'units': 9999},
        }

        result = {t[0]: [] for t in Booking.BOOKING_TYPES}

        day = start_date
        while day <= end_date:
            for tkey, _ in Booking.BOOKING_TYPES:
                cfg = capacity.get(tkey, {'units': 9999})
                units = cfg['units']
                count = Booking.objects.filter(check_in__lte=day, check_out__gt=day, type=tkey).count()
                if count >= units:
                    result[tkey].append(day.isoformat())
            day = day + timedelta(days=1)

        return Response(result, status=status.HTTP_200_OK)


class SafariAvailabilityView(APIView):
    """
    Return safari slot bookings for a given date.
    Endpoint: GET /api/safari-availability/?date=YYYY-MM-DD
    Response example:
    {
      "2025-12-11": {"morning": 10, "midday": 8, "afternoon": 12}
    }
    """

    def get(self, request):
        date_q = request.query_params.get('date')
        if not date_q:
            return Response({'message': 'Missing required parameter: date'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target = date.fromisoformat(date_q)
        except Exception:
            return Response({'message': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        # Count guests per slot (exclude cancelled)
        result_slots = {}
        from django.db.models import Sum
        for slot_key, _ in Booking.SAFARI_SLOTS:
            qs = Booking.objects.filter(type='safari', safari_slot=slot_key, check_in=target).exclude(status='cancelled')
            agg = qs.aggregate(total=Sum('guests'))
            result_slots[slot_key] = agg.get('total') or 0

        return Response({date_q: result_slots}, status=status.HTTP_200_OK)


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')
class StaffDashboardView(TemplateView):
    """
    Simple staff-only dashboard. Place behind a non-obvious URL in project urls.
    Template: bookings/staff_dashboard.html
    """
    template_name = 'bookings/staff_dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Show recent bookings and counts for quick overview
        ctx['recent_bookings'] = Booking.objects.order_by('-created_at')[:25]
        ctx['counts_by_type'] = {t[0]: Booking.objects.filter(type=t[0]).count() for t in Booking.BOOKING_TYPES}
        ctx['cancelled_count'] = Booking.objects.filter(status='cancelled').count()
        # Include recent booking requests from contact app, if present
        try:
            from contact.models import BookingRequest

            ctx['recent_booking_requests'] = BookingRequest.objects.order_by('-created_at')[:25]
        except Exception:
            ctx['recent_booking_requests'] = []
        return ctx
