from django.urls import path
from .views import BookingListCreateView, AvailabilityCheckView, BookingDetailView, BookingCancelView

app_name = 'bookings'

urlpatterns = [
    path('', BookingListCreateView.as_view(), name='booking-list-create'),
    path('availability/', AvailabilityCheckView.as_view(), name='availability-check'),
    path('<str:confirmation_number>/cancel/', BookingCancelView.as_view(), name='booking-cancel'),
    path('<str:confirmation_number>/', BookingDetailView.as_view(), name='booking-detail'),
]
