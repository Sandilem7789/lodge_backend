from rest_framework import serializers
from .models import ContactMessage
from .models import BookingRequest


class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer for ContactMessage model with email and required field validation.
    """

    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'phone', 'subject', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_email(self, value):
        """Validate email format."""
        if not value:
            raise serializers.ValidationError("Email is required.")
        return value

    def validate_name(self, value):
        """Validate name is provided."""
        if not value or not value.strip():
            raise serializers.ValidationError("Name is required.")
        return value.strip()

    def validate_subject(self, value):
        """Validate subject is provided."""
        if not value or not value.strip():
            raise serializers.ValidationError("Subject is required.")
        return value.strip()

    def validate_message(self, value):
        """Validate message is provided."""
        if not value or not value.strip():
            raise serializers.ValidationError("Message is required.")
        return value.strip()


class BookingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingRequest
        fields = [
            'id', 'name', 'email', 'phone', 'type', 'check_in', 'check_out', 'guests', 'message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError('Email is required')
        return value
