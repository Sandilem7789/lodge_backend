from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ContactMessage
from .serializers import ContactSerializer
from .serializers import BookingRequestSerializer
from .models import BookingRequest
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test


class BookingRequestCreateView(APIView):
    """Create booking enquiries via contact form (public)."""

    def post(self, request):
        serializer = BookingRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Booking request received.', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Failed to create booking request.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')
class BookingRequestListView(APIView):
    """Staff-only view to list booking requests."""

    def get(self, request):
        qs = BookingRequest.objects.order_by('-created_at')
        serializer = BookingRequestSerializer(qs, many=True)
        return Response({'count': qs.count(), 'data': serializer.data}, status=status.HTTP_200_OK)


class ContactCreateView(APIView):
    """
    Handle POST requests to submit contact form messages.
    Endpoint: POST /api/contact/
    """

    def post(self, request):
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'message': 'Contact message received successfully.',
                    'data': {
                        'id': serializer.data['id'],
                        'name': serializer.data['name'],
                        'email': serializer.data['email'],
                        'created_at': serializer.data['created_at'],
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                'message': 'Failed to submit contact message.',
                'errors': serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
