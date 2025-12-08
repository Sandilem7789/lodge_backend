from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.db.models import Q
from .models import Booking
from .serializers import BookingSerializer, AvailabilitySerializer


class BookingCreateView(APIView):
    """
    Handle POST requests to create new bookings.
    Endpoint: POST /api/bookings/
    """

    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'message': 'Booking created successfully.',
                    'data': serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                'message': 'Failed to create booking.',
                'errors': serializer.errors,
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
        """List all bookings."""
        bookings = Booking.objects.all()
        serializer = BookingSerializer(bookings, many=True)
        return Response(
            {
                'message': 'Bookings retrieved successfully.',
                'count': bookings.count(),
                'data': serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create a new booking."""
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'message': 'Booking created successfully.',
                    'data': serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                'message': 'Failed to create booking.',
                'errors': serializer.errors,
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

        booking.status = 'cancelled'
        booking.save()

        serializer = BookingSerializer(booking)
        return Response(
            {
                'message': 'Booking cancelled successfully.',
                'data': serializer.data,
            },
            status=status.HTTP_200_OK,
        )
