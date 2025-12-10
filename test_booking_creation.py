#!/usr/bin/env python
"""
Quick test script to verify booking creation returns confirmation_number and other key fields.
Run: python test_booking_creation.py
"""
import os
import django
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lodge_backend.settings')
django.setup()

from bookings.models import Booking
from bookings.serializers import BookingSerializer

def test_booking_creation():
    """Test that booking creation returns confirmation_number and key fields."""
    
    # Create test booking data
    tomorrow = date.today() + timedelta(days=1)
    day_after = date.today() + timedelta(days=3)
    
    booking_data = {
        'type': 'chalet',
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '123456789',
        'check_in': tomorrow,
        'check_out': day_after,
        'guests': 2,
        'message': 'Looking forward to my stay!'
    }
    
    # Validate and save using serializer
    serializer = BookingSerializer(data=booking_data)
    
    if serializer.is_valid():
        booking = serializer.save()
        print("✅ Booking created successfully!")
        print("\n📋 Serialized Response Data:")
        print("=" * 60)
        
        import json
        response_data = serializer.data
        print(json.dumps(response_data, indent=2, default=str))
        
        print("\n" + "=" * 60)
        print("\n✅ Key fields present in response:")
        
        required_fields = [
            'confirmation_number',
            'status',
            'type',
            'name',
            'email',
            'phone',
            'check_in',
            'check_out',
            'guests',
            'message'
        ]
        
        for field in required_fields:
            if field in response_data:
                print(f"   ✓ {field}: {response_data[field]}")
            else:
                print(f"   ✗ {field}: MISSING")
        
        # Cleanup
        booking.delete()
        print("\n✅ Test booking cleaned up from database.")
        
    else:
        print("❌ Serializer validation failed:")
        print(serializer.errors)

if __name__ == '__main__':
    test_booking_creation()
