from rest_framework import serializers
from .models import Subscriber


class SubscriberSerializer(serializers.ModelSerializer):
    """
    Serializer for Subscriber model with email validation and duplicate handling.
    """

    class Meta:
        model = Subscriber
        fields = ['id', 'email', 'subscribed_at']
        read_only_fields = ['id', 'subscribed_at']

    def validate_email(self, value):
        """Validate email format and uniqueness."""
        if not value:
            raise serializers.ValidationError("Email is required.")

        # Check if email already exists
        if Subscriber.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "This email is already subscribed to our newsletter."
            )

        return value
