from django.urls import path
from .views import (
    OrderListView,
    initialize_payment,
    verify_payment,
    itn_notification,
)

app_name = 'payfast'

urlpatterns = [
    # Payment initialization — returns PayFast form params
    path('payments/initialize/', initialize_payment, name='initialize_payment'),

    # Payment verification — check if ITN has confirmed the order
    path('payments/verify/', verify_payment, name='verify_payment'),

    # PayFast ITN (Instant Transaction Notification) server-to-server callback
    path('payments/notify/', itn_notification, name='itn_notification'),

    # Order list (staff)
    path('orders/', OrderListView.as_view(), name='orders-list'),
]
