from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ContactMessage
from .serializers import ContactSerializer


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
