from django.urls import path
from .views import BookingCreateView, AvailabilityCheckView, BookingDetailView

app_name = 'bookings'

urlpatterns = [
    path('', BookingCreateView.as_view(), name='booking-create'),
    path('availability/', AvailabilityCheckView.as_view(), name='availability-check'),
    path('<str:confirmation_number>/', BookingDetailView.as_view(), name='booking-detail'),
]
