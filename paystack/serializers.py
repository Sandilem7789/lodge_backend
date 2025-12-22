from rest_framework import serializers
from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model."""
    
    class Meta:
        model = Order
        fields = [
            'id',
            'order_id',
            'booking',
            'amount',
            'currency',
            'status',
            'reference',
            'email',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'order_id', 'reference', 'created_at', 'updated_at']
