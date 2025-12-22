from django.db import models
from bookings.models import Booking
import uuid


class Order(models.Model):
    """Paystack payment order model."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Fields
    order_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='order')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount in ZAR")
    currency = models.CharField(max_length=3, default='ZAR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=100, blank=True, null=True, unique=True, help_text="Paystack transaction reference")
    email = models.EmailField(help_text="Customer email for payment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.order_id} - {self.status} (ZAR {self.amount})"
