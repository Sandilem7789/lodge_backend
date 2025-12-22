"""
URL configuration for lodge_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from bookings.views import StaffDashboardView, AvailabilityCalendarView, SafariAvailabilityView
from paystack import views as paystack_views
from lodge_backend.dashboard_views import PricesView, ReportsView, SettingsView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Secret staff dashboard (not /admin) - restrict access to staff users
    path('staff-area-9f3b7d3a-portal/', StaffDashboardView.as_view(), name='staff-dashboard'),
    # Global availability calendar for frontend to disable fully-booked dates
    path('api/availability/', AvailabilityCalendarView.as_view(), name='availability-calendar'),
    # Safari slot availability per date
    path('api/safari-availability/', SafariAvailabilityView.as_view(), name='safari-availability'),
    path('api/bookings/', include('bookings.urls')),
    path('api/contact/', include('contact.urls')),
    path('api/newsletter/', include('newsletter.urls')),
    path('api/paystack/', include('paystack.urls')),
    # Compatibility routes for frontend expecting /api/payments/ endpoints
    path('api/payments/initialize/', paystack_views.initialize_payment, name='initialize_payment'),
    path('api/payments/verify/', paystack_views.verify_payment, name='verify_payment'),
    # Dashboard endpoints
    path('api/prices/', PricesView.as_view(), name='prices'),
    path('api/reports/', ReportsView.as_view(), name='reports'),
    path('api/settings/', SettingsView.as_view(), name='settings'),
]
