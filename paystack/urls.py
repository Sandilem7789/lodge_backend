from django.urls import path
from .views import (
    InitializePaymentView,
    PaystackCallbackView,
    PaymentConfirmationView,
    OrderListView,
    booking_confirmation,
    initialize_payment,
    verify_payment,
)

app_name = 'paystack'

urlpatterns = [
    # Payment initialization (start payment flow)
    path('initialize-payment/', InitializePaymentView.as_view(), name='initialize-payment'),

    # Match frontend service module
    path('payments/initialize/', initialize_payment, name='initialize_payment'),
    
    # POST endpoint for payment verification
    path('payments/verify/', verify_payment, name='verify_payment'),

    # Paystack callback (verification after redirect) - GET endpoint
    path('callback/', PaystackCallbackView.as_view(), name='callback'),

    # Confirmation page (show payment result)
    path('confirmation/<str:order_id>/', PaymentConfirmationView.as_view(), name='confirmation'),

    # HTML booking confirmation page shown after successful payment
    path('booking-confirmation/<str:order_id>/', booking_confirmation, name='booking-confirmation'),

    # List orders (admin/staff)
    path('orders/', OrderListView.as_view(), name='orders-list'),
]
