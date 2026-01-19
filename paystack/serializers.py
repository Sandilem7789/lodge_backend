from rest_framework import serializers
from .models import Order
from .utils import get_display_amount


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model."""
    
    # Override amount field to ensure it's returned in ZAR (rand)
    amount = serializers.SerializerMethodField()
    
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
    
    def get_amount(self, obj):
        """Return amount in ZAR (rand) for frontend display."""
        return get_display_amount(obj.amount)
