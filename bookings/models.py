from django.db import models

class Booking(models.Model):
    BOOKING_TYPES = [
        ('chalet', 'Chalet'),
        ('campsite', 'Campsite'),
        ('conference', 'Conference'),
        ('event', 'Event'),
        ('safari', 'Safari Drive'),
    ]
    type = models.CharField(max_length=20, choices=BOOKING_TYPES)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)
    guests = models.PositiveIntegerField(default=1)
    message = models.TextField(blank=True)
    confirmation_number = models.CharField(max_length=50, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
