from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Subscriber
from .serializers import SubscriberSerializer


class SubscriberCreateView(APIView):
    """
    Handle POST requests to subscribe to the newsletter.
    Endpoint: POST /api/newsletter/subscribe/
    """

    def post(self, request):
        serializer = SubscriberSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'message': 'Successfully subscribed to newsletter.',
                    'data': {
                        'id': serializer.data['id'],
                        'email': serializer.data['email'],
                        'subscribed_at': serializer.data['subscribed_at'],
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                'message': 'Failed to subscribe to newsletter.',
                'errors': serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
