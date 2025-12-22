"""
Dashboard API endpoints for staff management.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from bookings.models import Booking
from bookings.pricing import get_seasonal_rates
from paystack.models import Order
from django.conf import settings


class PricesView(APIView):
    """
    Return current fixed rates for each booking type and season.
    GET /api/prices/
    """
    
    def get(self, request):
        try:
            rates = get_seasonal_rates()
            return Response({
                'success': True,
                'data': rates
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportsView(APIView):
    """
    Return aggregated revenue and occupancy data.
    GET /api/reports/
    
    Query parameters:
    - start_date: YYYY-MM-DD (optional, defaults to 30 days ago)
    - end_date: YYYY-MM-DD (optional, defaults to today)
    """
    
    def get(self, request):
        try:
            # Get date range from query params
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            
            if start_date_str:
                try:
                    start_date = date.fromisoformat(start_date_str)
                except ValueError:
                    return Response({
                        'success': False,
                        'error': 'Invalid start_date format. Use YYYY-MM-DD.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                start_date = date.today() - timedelta(days=30)
            
            if end_date_str:
                try:
                    end_date = date.fromisoformat(end_date_str)
                except ValueError:
                    return Response({
                        'success': False,
                        'error': 'Invalid end_date format. Use YYYY-MM-DD.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                end_date = date.today()
            
            # Revenue data (from paid orders)
            paid_orders = Order.objects.filter(
                status='paid',
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
            
            total_revenue = paid_orders.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
            
            revenue_by_type = {}
            for booking_type, _ in Booking.BOOKING_TYPES:
                type_orders = paid_orders.filter(booking__type=booking_type)
                type_revenue = type_orders.aggregate(
                    total=Sum('amount')
                )['total'] or Decimal('0.00')
                revenue_by_type[booking_type] = {
                    'revenue': float(type_revenue),
                    'count': type_orders.count()
                }
            
            # Occupancy data (from bookings)
            bookings = Booking.objects.filter(
                check_in__lte=end_date,
                check_out__gte=start_date
            ).exclude(status='cancelled')
            
            occupancy_by_type = {}
            total_nights = 0
            
            for booking_type, _ in Booking.BOOKING_TYPES:
                type_bookings = bookings.filter(type=booking_type)
                type_nights = 0
                
                for booking in type_bookings:
                    if booking.check_in and booking.check_out:
                        # Calculate nights within the date range
                        check_in = max(booking.check_in, start_date)
                        check_out = min(booking.check_out, end_date)
                        if check_out > check_in:
                            type_nights += (check_out - check_in).days
                    elif booking.type in ['safari', 'conference', 'event']:
                        # Flat rate bookings count as 1
                        type_nights += 1
                
                occupancy_by_type[booking_type] = {
                    'nights': type_nights,
                    'bookings': type_bookings.count()
                }
                total_nights += type_nights
            
            # Booking status summary
            status_summary = {}
            for status_code, _ in Booking.STATUS_CHOICES:
                status_summary[status_code] = Booking.objects.filter(
                    created_at__date__gte=start_date,
                    created_at__date__lte=end_date,
                    status=status_code
                ).count()
            
            # Payment status summary
            payment_status_summary = {}
            for status_code, _ in Order.STATUS_CHOICES:
                payment_status_summary[status_code] = Order.objects.filter(
                    created_at__date__gte=start_date,
                    created_at__date__lte=end_date,
                    status=status_code
                ).count()
            
            return Response({
                'success': True,
                'data': {
                    'period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                    },
                    'revenue': {
                        'total': float(total_revenue),
                        'by_type': revenue_by_type,
                    },
                    'occupancy': {
                        'total_nights': total_nights,
                        'by_type': occupancy_by_type,
                    },
                    'bookings': {
                        'status_summary': status_summary,
                        'total': sum(status_summary.values()),
                    },
                    'payments': {
                        'status_summary': payment_status_summary,
                        'total': sum(payment_status_summary.values()),
                    },
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SettingsView(APIView):
    """
    Return lodge contact info and Paystack public key.
    GET /api/settings/
    """
    
    def get(self, request):
        try:
            # Get Paystack public key from settings
            paystack_public_key = getattr(settings, 'PAYSTACK_PUBLIC_KEY', '')
            
            # Lodge contact info (can be moved to settings or database later)
            lodge_info = {
                'name': 'Ikhaya Lami Lodge',
                'email': 'info@ikhayalami.co.za',  # Update with actual email
                'phone': '+27 12 345 6789',  # Update with actual phone
                'address': 'Lodge Address, City, Province, South Africa',  # Update with actual address
            }
            
            return Response({
                'success': True,
                'data': {
                    'lodge': lodge_info,
                    'paystack': {
                        'public_key': paystack_public_key,
                        'currency': getattr(settings, 'PAYSTACK_CURRENCY', 'ZAR'),
                    }
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


