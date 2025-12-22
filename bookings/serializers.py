from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Booking
from django.db.models import Sum


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
            'safari_slot',
            'message',
            'status',
            'cancelled_at',
            'cancellation_reason',
            'confirmation_number',
            'amount',
            'created_at',
        ]
        read_only_fields = ['id', 'confirmation_number', 'created_at', 'cancelled_at', 'amount']

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

        # Capacity rules per booking type (units = number of separate bookable units)
        # and per-booking guest limits. Adjust units if facility counts change.
        capacity = {
            'chalet': {'units': 3, 'min': 1, 'max': 4},
            'campsite': {'units': 10, 'min': 1, 'max': 7},
            'conference': {'units': 1, 'min': 1, 'max': 11},
            # Safari: 3 vehicles, 7-10 guests per booking, max daily capacity 30
            'safari': {'units': 3, 'min': 7, 'max': 10, 'daily_max': 30},
            'event': {'units': 9999, 'min': 1, 'max': 9999},
        }

        booking_type = data.get('type')
        # Enforce per-booking guest constraints
        if booking_type in capacity and guests is not None:
            cfg = capacity[booking_type]
            if guests < cfg['min'] or guests > cfg['max']:
                raise serializers.ValidationError(
                    f"'{booking_type}' bookings must have between {cfg['min']} and {cfg['max']} guests."
                )

        # Special handling for safari bookings: require safari_slot and enforce slot/day capacity
        if booking_type == 'safari':
            safari_slot = data.get('safari_slot')
            if not safari_slot:
                raise serializers.ValidationError({'safari_slot': 'Safari bookings require a time slot (morning|midday|afternoon).'})

            # Use check_in as the safari date
            if not check_in:
                raise serializers.ValidationError({'check_in': 'Safari bookings require a check_in date.'})

            # Calculate existing booked guests for that date and slot (exclude cancelled)
            existing_qs = Booking.objects.filter(
                type='safari',
                safari_slot=safari_slot,
                check_in=check_in,
            ).exclude(status='cancelled')
            agg = existing_qs.aggregate(total=Sum('guests'))
            existing_total = agg.get('total') or 0

            daily_max = capacity['safari']['daily_max']
            if existing_total + guests > daily_max:
                raise serializers.ValidationError({
                    'non_field_errors': ["Selected time slot is fully booked"]
                })

        # Enforce per-date unit availability for other booking types (by counting overlapping bookings)
        if booking_type != 'safari' and booking_type and check_in and check_out:
            cfg = capacity.get(booking_type)
            if cfg:
                units = cfg['units']
                # iterate nights from check_in to day before check_out
                day = check_in
                while day < check_out:
                    overlapping = Booking.objects.filter(
                        type=booking_type,
                        check_in__lte=day,
                        check_out__gt=day,
                    ).count()
                    if overlapping >= units:
                        raise serializers.ValidationError(
                            {"non_field_errors": [f"No availability for {booking_type} on {day}. Fully booked."]}
                        )
                    day = day + timedelta(days=1)

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
