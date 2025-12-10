#!/usr/bin/env python
"""
Create sample bookings and test grouped endpoint and cancellation reason handling.
"""
import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lodge_backend.settings')
django.setup()

from django.test import Client
from bookings.models import Booking

client = Client()

# Create two bookings via serializer / API (bypass auth)
base_url = '/api/bookings/'

booking1 = {
    'type': 'chalet',
    'name': 'Alpha',
    'email': 'alpha@example.com',
    'phone': '111',
    'check_in': str(date.today() + timedelta(days=2)),
    'check_out': str(date.today() + timedelta(days=4)),
    'guests': 2,
    'message': 'Test 1'
}
booking2 = {
    'type': 'campsite',
    'name': 'Beta',
    'email': 'beta@example.com',
    'phone': '222',
    'check_in': str(date.today() + timedelta(days=5)),
    'check_out': str(date.today() + timedelta(days=7)),
    'guests': 4,
    'message': 'Test 2'
}

resp1 = client.post(base_url, booking1, content_type='application/json')
resp2 = client.post(base_url, booking2, content_type='application/json')
print('POST1 status', resp1.status_code, resp1.json())
print('POST2 status', resp2.status_code, resp2.json())

# Call grouped endpoint
grp = client.get(base_url + 'grouped/')
print('GROUPED', grp.status_code, grp.json())

# Cancel booking1 with reason
cn = resp1.json()['data']['confirmation_number']
cancel_resp = client.patch(f'{base_url}{cn}/cancel/', data='{"cancellation_reason":"Client request"}', content_type='application/json')
print('CANCEL', cancel_resp.status_code, cancel_resp.json())

# Clean up
Booking.objects.filter(email__in=['alpha@example.com','beta@example.com']).delete()
print('Cleaned up')
