from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'booking', 'amount', 'status', 'reference', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_id', 'reference', 'booking__confirmation_number')
    readonly_fields = ('order_id', 'reference', 'created_at', 'updated_at')
