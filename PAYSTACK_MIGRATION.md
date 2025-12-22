# Paystack Migration Summary

**Date:** December 19, 2025  
**Project:** Ikhaya Lami Lodge Backend  
**Migration:** PayFast → Paystack  
**Status:** ✅ Complete & Ready for Testing

---

## What Was Implemented

### 1. ✅ New `paystack` Django App

Created a complete payment application with:
- **Model:** `Order` — tracks payment transactions
- **Views:** 4 RESTful endpoints
- **Serializers:** Order serialization
- **URLs:** Payment routes
- **Admin:** Order management interface
- **Logging:** Detailed payment debugging

### 2. ✅ Environment Configuration

**File:** `.env` (in backend directory)
```env
PAYSTACK_SECRET_KEY=sk_test_xxxxxxxxxxxxx
PAYSTACK_PUBLIC_KEY=pk_test_xxxxxxxxxxxxx
PAYSTACK_CURRENCY=ZAR
```

**Loaded in settings.py via `python-decouple`:**
```python
from decouple import config
PAYSTACK_SECRET_KEY = config('PAYSTACK_SECRET_KEY', default='')
PAYSTACK_PUBLIC_KEY = config('PAYSTACK_PUBLIC_KEY', default='')
PAYSTACK_CURRENCY = config('PAYSTACK_CURRENCY', default='ZAR')
```

### 3. ✅ Paystack API Integration

#### InitializePaymentView (POST)
- Creates `Order` record (status: pending)
- Calls Paystack `/transaction/initialize` API
- Returns `authorization_url` for redirect checkout
- Logs all payloads for debugging

**Request:**
```json
{
  "booking_id": 123,
  "email": "customer@example.com",
  "callback_url": "https://yourdomain.com/payment-callback/"
}
```

**Response:**
```json
{
  "message": "Payment initialized successfully",
  "data": {
    "order_id": "550e8400-e29b-41d4-a716-446655440000",
    "amount": 1600.00,
    "currency": "ZAR",
    "authorization_url": "https://checkout.paystack.com/...",
    "reference": "paystack_reference_xxxx"
  }
}
```

#### PaystackCallbackView (GET)
- Receives callback from Paystack with transaction reference
- Calls Paystack `/transaction/verify/{reference}` API
- Updates `Order.status` (paid/failed)
- Redirects to confirmation or failure page

#### PaymentConfirmationView (GET)
- Displays payment confirmation details
- Returns Order + Booking information

#### OrderListView (GET)
- Lists all payment orders
- Supports filtering by status or booking_id

### 4. ✅ Database Integration

**Order Model Fields:**
```
order_id         → UUID (unique)
booking          → OneToOneField (Booking)
amount           → DecimalField (ZAR)
currency         → CharField (ZAR)
status           → CharField (pending|paid|failed|cancelled)
reference        → CharField (Paystack transaction reference)
email            → EmailField (customer email)
created_at       → DateTimeField (auto)
updated_at       → DateTimeField (auto)
```

**Migration Applied:** `paystack/migrations/0001_initial.py` ✅

### 5. ✅ Logging & Debugging

**Configuration (settings.py):**
```python
LOGGING = {
    'loggers': {
        'paystack': {
            'handlers': ['console', 'paystack_file'],
            'level': 'DEBUG',
        },
    },
}
```

**Log Files:**
- `logs/django.log` — General application logs
- `logs/paystack.log` — Payment-specific logs (DEBUG level)

**Sample Logs:**
```
INFO Initializing Paystack payment for order 550e8400-e29b-41d4-a716-446655440000
DEBUG Paystack payload: {"email": "...", "amount": 160000, ...}
INFO Paystack initialize response: {"status": true, "data": {...}}
INFO Processing Paystack callback for reference: paystack_ref_xxx
INFO Order 550e8400-e29b-41d4-a716-446655440000 marked as paid
```

### 6. ✅ URL Routes

**Project level (lodge_backend/urls.py):**
```python
path('api/paystack/', include('paystack.urls')),
```

**Paystack routes (paystack/urls.py):**
```
POST   /api/paystack/initialize-payment/       → InitializePaymentView
GET    /api/paystack/callback/?reference=...   → PaystackCallbackView
GET    /api/paystack/confirmation/<order_id>/  → PaymentConfirmationView
GET    /api/paystack/orders/                   → OrderListView
```

### 7. ✅ Admin Interface

Order management available at `/admin/paystack/order/`
- List orders by date, status, booking
- Search by order_id, reference, email
- Filter by payment status

### 8. ✅ Amount Calculation

**Pricing Configuration (customizable):**
```python
pricing = {
    'chalet': 800.00,       # ZAR per night
    'campsite': 200.00,     # ZAR per night
    'conference': 5000.00,  # ZAR flat
    'safari': 2500.00,      # ZAR flat (one-time)
    'event': 1000.00,       # ZAR flat
}
```

For multi-night bookings: `base_price * number_of_nights`

**Update in:** `paystack/views.py` → `InitializePaymentView._calculate_amount()`

---

## File Structure

```
paystack/
├── __init__.py              # App initialization
├── apps.py                  # App configuration
├── admin.py                 # Admin order management
├── models.py                # Order model
├── serializers.py           # Order serializer
├── views.py                 # Payment views (460+ lines)
│   ├── InitializePaymentView (handles initialize-payment)
│   ├── PaystackCallbackView (handles verification)
│   ├── PaymentConfirmationView (shows confirmation)
│   └── OrderListView (lists orders)
├── urls.py                  # Payment routes
├── tests.py                 # Unit tests (placeholder)
└── migrations/
    └── 0001_initial.py      # Order model migration

.env                         # Environment variables
logs/paystack.log            # Payment logs
```

---

## Testing Checklist

- [x] App structure created
- [x] Models defined and migrated
- [x] Views implemented with Paystack API calls
- [x] URLs configured
- [x] Settings updated with environment variables
- [x] Logging configured
- [x] Django system checks pass
- [x] Admin interface registered

### Next Steps: Manual Testing

1. **Update .env with real test keys:**
   ```bash
   # Get from https://dashboard.paystack.com/settings/developer
   PAYSTACK_SECRET_KEY=sk_test_your_actual_key
   PAYSTACK_PUBLIC_KEY=pk_test_your_actual_key
   ```

2. **Test Payment Initialization:**
   ```bash
   curl -X POST http://localhost:8000/api/paystack/initialize-payment/ \
     -H "Content-Type: application/json" \
     -d '{
       "booking_id": 1,
       "email": "test@example.com",
       "callback_url": "http://localhost:3000/payment-callback"
     }'
   ```

3. **Test with Paystack Test Cards:**
   - Success: `4084084084084081` (12/25, 123)
   - Failure: `5555555555554444` (12/25, 123)

4. **Verify Logs:**
   ```bash
   tail -f logs/paystack.log
   ```

5. **Check Admin Orders:**
   - Go to `/admin/paystack/order/`
   - Should see payment records

---

## Frontend Integration

### Example: Initialize Payment

```typescript
// frontend/src/api.ts
export const initializePayment = async (
  bookingId: number,
  email: string,
  callbackUrl: string
) => {
  const response = await fetch('/api/paystack/initialize-payment/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      booking_id: bookingId,
      email,
      callback_url: callbackUrl,
    }),
  });
  const data = await response.json();
  if (data.data?.authorization_url) {
    window.location.href = data.data.authorization_url;
  }
  return data;
};
```

### Example: Payment Button Component

```typescript
// frontend/src/components/PaymentButton.tsx
export const PaymentButton: React.FC<{ 
  bookingId: number; 
  email: string 
}> = ({ bookingId, email }) => {
  const handlePayment = async () => {
    const callbackUrl = `${window.location.origin}/payment-callback`;
    await initializePayment(bookingId, email, callbackUrl);
  };

  return (
    <button onClick={handlePayment} className="btn-primary">
      Proceed to Paystack
    </button>
  );
};
```

---

## Production Deployment

### Before Going Live

1. **Update keys to live mode:**
   ```env
   PAYSTACK_SECRET_KEY=sk_live_your_live_key
   PAYSTACK_PUBLIC_KEY=pk_live_your_live_key
   ```

2. **Enable HTTPS (required by Paystack):**
   ```python
   # settings.py
   DEBUG = False
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
   ```

3. **Configure Paystack webhook (optional):**
   - Paystack Dashboard → Settings → Webhooks
   - Add: `https://yourdomain.com/api/paystack/webhook/` (if implementing)

4. **Test with live cards (provided by Paystack)**

5. **Monitor logs:**
   ```bash
   tail -f logs/paystack.log
   ```

---

## Documentation Files

### Created:
- **[PAYSTACK_INTEGRATION.md](PAYSTACK_INTEGRATION.md)** — Comprehensive guide with:
  - Setup instructions
  - API endpoint reference
  - Database models
  - Payment flow diagrams
  - Logging & debugging
  - Frontend examples
  - Test card numbers
  - Production checklist

- **[SERVER_BLUEPRINT.md](SERVER_BLUEPRINT.md)** — Updated with:
  - Paystack models section
  - Payment endpoints table
  - URL routing for Paystack
  - Payment integration overview

---

## Summary

✅ **Paystack integration is complete and ready for testing.**

The backend now:
- Accepts booking payments via Paystack redirect checkout
- Verifies transactions securely
- Stores payment records in the database
- Provides logs for debugging
- Has admin interface for managing orders
- Loads configuration from environment variables

**Next:** Update frontend to call `/api/paystack/initialize-payment/` and handle the redirect checkout flow.

---

## Support

For detailed information, see:
- [PAYSTACK_INTEGRATION.md](PAYSTACK_INTEGRATION.md) — Full integration guide
- [SERVER_BLUEPRINT.md](SERVER_BLUEPRINT.md) — Complete API reference
- Paystack Docs: https://paystack.com/docs/payments/

Questions? Check logs: `logs/paystack.log`
