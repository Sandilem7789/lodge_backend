from django.db import models

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class BookingRequest(models.Model):
    """Stores booking enquiries submitted via the contact form for staff to review."""
    BOOKING_TYPES = [
        ('chalet', 'Chalet'),
        ('campsite', 'Campsite'),
        ('conference', 'Conference'),
        ('event', 'Event'),
        ('safari', 'Safari Drive'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    type = models.CharField(max_length=20, choices=BOOKING_TYPES)
    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)
    guests = models.PositiveIntegerField(default=1)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request {self.id} - {self.name} ({self.type})"
