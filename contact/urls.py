from django.urls import path
from .views import ContactCreateView, BookingRequestCreateView, BookingRequestListView

app_name = 'contact'

urlpatterns = [
    path('', ContactCreateView.as_view(), name='contact-create'),
    path('booking-requests/', BookingRequestCreateView.as_view(), name='booking-request-create'),
    path('booking-requests/list/', BookingRequestListView.as_view(), name='booking-request-list'),
]
