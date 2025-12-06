from django.urls import path
from .views import SubscriberCreateView

app_name = 'newsletter'

urlpatterns = [
    path('subscribe/', SubscriberCreateView.as_view(), name='subscriber-create'),
]
