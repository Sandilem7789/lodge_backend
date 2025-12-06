from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for Booking model with validation for check-in/check-out dates
    and automatic confirmation number generation.
    """

    class Meta:
        model = Booking
        fields = [
            'id',
            'type',
            'name',
            'email',
            'phone',
            'check_in',
            'check_out',
            'guests',
            'message',
            'confirmation_number',
            'created_at',
        ]
        read_only_fields = ['id', 'confirmation_number', 'created_at']

    def validate_email(self, value):
        """Validate email format."""
        if not value:
            raise serializers.ValidationError("Email is required.")
        return value

    def validate_phone(self, value):
        """Validate phone number is provided."""
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        return value

    def validate(self, data):
        """
        Validate booking data:
        - check_in must be before check_out
        - check_in cannot be in the past
        - guests must be at least 1
        """
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        guests = data.get('guests')

        if check_in and check_out:
            if check_in >= check_out:
                raise serializers.ValidationError(
                    "Check-in date must be before check-out date."
                )

            # Check that dates are not in the past
            today = timezone.now().date()
            if check_in < today:
                raise serializers.ValidationError(
                    "Check-in date cannot be in the past."
                )

        if guests and guests < 1:
            raise serializers.ValidationError(
                "Number of guests must be at least 1."
            )

        return data

    def create(self, validated_data):
        """Generate confirmation number on booking creation."""
        # Generate a simple confirmation number (can be enhanced with UUID or custom logic)
        import uuid
        validated_data['confirmation_number'] = str(uuid.uuid4())[:12].upper()
        return super().create(validated_data)


class AvailabilitySerializer(serializers.Serializer):
    """Serializer for checking availability."""
    type = serializers.ChoiceField(
        choices=['chalet', 'campsite', 'conference', 'event', 'safari']
    )
    check_in = serializers.DateField()
    check_out = serializers.DateField()

    def validate(self, data):
        """Validate dates."""
        check_in = data.get('check_in')
        check_out = data.get('check_out')

        if check_in >= check_out:
            raise serializers.ValidationError(
                "Check-in date must be before check-out date."
            )

        today = timezone.now().date()
        if check_in < today:
            raise serializers.ValidationError(
                "Check-in date cannot be in the past."
            )

        return data
