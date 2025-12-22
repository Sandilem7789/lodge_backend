# Paystack Payment Integration Guide

**Framework:** Django REST Framework  
**Payment Gateway:** Paystack  
**Currency:** ZAR (South African Rand)  
**Status:** Development (Test Mode)

---

## Overview

This guide documents the Paystack payment integration for the Ikhaya Lami Lodge backend. The system handles booking payments using Paystack's redirect checkout flow.

---

## Setup & Configuration

### 1. Environment Variables (.env)

Located in `lodge_backend/.env`:

```env
# Paystack Payment Keys (from https://dashboard.paystack.com/settings/developer)
PAYSTACK_SECRET_KEY=sk_test_xxxxxxxxxxxxx  # Replace with your test secret key
PAYSTACK_PUBLIC_KEY=pk_test_xxxxxxxxxxxxx  # Replace with your test public key
PAYSTACK_CURRENCY=ZAR                      # Currency code
```

**Obtaining Keys:**
1. Sign up on [Paystack](https://paystack.com)
2. Go to **Settings → Developer** in dashboard
3. Copy your **Secret Key** and **Public Key** (for test mode, use `sk_test_*` and `pk_test_*`)
4. Update `.env` with your keys

### 2. Django Settings (settings.py)

Paystack keys are loaded from `.env` using `python-decouple`:

```python
from decouple import config

PAYSTACK_SECRET_KEY = config('PAYSTACK_SECRET_KEY', default='')
PAYSTACK_PUBLIC_KEY = config('PAYSTACK_PUBLIC_KEY', default='')
PAYSTACK_CURRENCY = config('PAYSTACK_CURRENCY', default='ZAR')
```

### 3. Install Required Package

```bash
pip install python-decouple requests
```

---

## Database Models

### Order Model (`paystack/models.py`)

Stores payment transaction records linked to bookings.

```python
class Order(models.Model):
    order_id          # UUID (unique identifier)
    booking           # ForeignKey to Booking
    amount            # DecimalField (ZAR)
    currency          # CharField (default: ZAR)
    status            # CharField (pending|paid|failed|cancelled)
    reference         # CharField (Paystack transaction reference)
    email             # EmailField (customer email)
    created_at        # DateTimeField (auto)
    updated_at        # DateTimeField (auto)
```

**Status Values:**
- `pending` — Order created, awaiting payment
- `paid` — Payment verified successfully
- `failed` — Payment failed or rejected
- `cancelled` — Order cancelled by customer

---

## API Endpoints

All endpoints are under `/api/paystack/`.

### 1. Initialize Payment

**Endpoint:** `POST /api/paystack/initialize-payment/`

**Purpose:** Start the payment flow by initializing a Paystack transaction.

**Request Payload:**
```json
{
  "booking_id": 123,
  "email": "customer@example.com",
  "callback_url": "https://yourdomain.com/payment-callback/"
}
```

**Response (Success - 201):**
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

**Response (Error - 400/404/503):**
```json
{
  "message": "Error description"
}
```

**Flow:**
1. Frontend calls this endpoint with booking_id, customer email, and callback URL
2. Backend creates an Order record (status: pending)
3. Backend calls Paystack `/transaction/initialize` API
4. Paystack returns `authorization_url` (payment page)
5. Frontend redirects user to `authorization_url`
6. User enters payment details and confirms

### 2. Paystack Callback

**Endpoint:** `GET /api/paystack/callback/?reference=<paystack_reference>`

**Purpose:** Verify payment after user completes payment on Paystack.

**Query Parameters:**
- `reference` (required) — Paystack transaction reference

**Process:**
1. User redirected here by Paystack after payment
2. Backend calls Paystack `/transaction/verify/{reference}` API
3. If transaction status == "success": Order.status = "paid"
4. If failed: Order.status = "failed"
5. Redirects to `/payment-confirmation/{order_id}/` or `/payment-failed/`

**Redirects:**
```
Success: /payment-confirmation/550e8400-e29b-41d4-a716-446655440000/
Failure: /payment-failed/?reference=paystack_reference_xxxx
Missing: /payment-failed/?message=Missing+reference
```

### 3. Payment Confirmation

**Endpoint:** `GET /api/paystack/confirmation/<order_id>/`

**Purpose:** Retrieve payment confirmation details.

**Response (200):**
```json
{
  "message": "Payment confirmed",
  "data": {
    "id": 1,
    "order_id": "550e8400-e29b-41d4-a716-446655440000",
    "amount": "1600.00",
    "currency": "ZAR",
    "status": "paid",
    "reference": "paystack_reference_xxxx",
    "email": "customer@example.com",
    "created_at": "2025-12-19T10:30:00Z",
    "updated_at": "2025-12-19T10:35:00Z"
  },
  "booking": {
    "confirmation_number": "ABC123XYZ",
    "type": "chalet",
    "check_in": "2025-12-25",
    "check_out": "2025-12-30",
    "guests": 4
  }
}
```

**Response (404):**
```json
{
  "message": "Order not found"
}
```

### 4. List Orders (Admin/Staff)

**Endpoint:** `GET /api/paystack/orders/`

**Purpose:** List all payment orders (staff-only endpoint).

**Query Parameters:**
- `status` (optional) — Filter by status (pending|paid|failed|cancelled)
- `booking_id` (optional) — Filter by booking ID

**Response (200):**
```json
{
  "message": "Orders retrieved successfully",
  "count": 15,
  "data": [
    {
      "id": 1,
      "order_id": "550e8400-e29b-41d4-a716-446655440000",
      "amount": "1600.00",
      "currency": "ZAR",
      "status": "paid",
      "reference": "paystack_reference_xxxx",
      "email": "customer@example.com",
      "created_at": "2025-12-19T10:30:00Z",
      "updated_at": "2025-12-19T10:35:00Z"
    }
  ]
}
```

---

## Payment Flow (Detailed)

### High-Level Sequence

```
1. Customer selects booking and proceeds to checkout
   ↓
2. Frontend calls POST /api/paystack/initialize-payment/
   ↓
3. Backend:
   - Creates Order record (status: pending)
   - Calls Paystack API to initialize transaction
   - Returns authorization_url
   ↓
4. Frontend redirects customer to Paystack checkout page
   ↓
5. Customer enters payment details and confirms
   ↓
6. Paystack processes payment and redirects to callback_url
   ↓
7. Backend calls GET /api/paystack/callback/?reference=...
   ↓
8. Backend verifies transaction with Paystack
   ↓
9. If successful: Order.status = "paid"
   Else: Order.status = "failed"
   ↓
10. Backend redirects to confirmation or failure page
   ↓
11. Frontend displays confirmation with booking details
```

### Amount Calculation

Amount is calculated based on booking type and duration:

```python
pricing = {
    'chalet': 800.00 ZAR/night,
    'campsite': 200.00 ZAR/night,
    'conference': 5000.00 ZAR (flat),
    'safari': 2500.00 ZAR (flat, one-time),
    'event': 1000.00 ZAR (flat),
}

# For multi-night bookings: base_price * num_nights
# For safari/single-day: base_price only
```

**Customize pricing in `paystack/views.py`:**
```python
def _calculate_amount(self, booking):
    # Update pricing dict here
    pricing = {
        'chalet': Decimal('800.00'),
        ...
    }
```

---

## Logging & Debugging

### Log Files

- **General logs:** `logs/django.log`
- **Payment logs:** `logs/paystack.log`

### Log Levels

```python
# INFO: Transaction initialization, verification results
# DEBUG: Full payloads and responses from Paystack
# ERROR: API failures, validation errors
```

### Sample Log Entries

**Initialize Payment:**
```
INFO Initializing Paystack payment for order 550e8400-e29b-41d4-a716-446655440000
DEBUG Paystack payload: {
  "email": "customer@example.com",
  "amount": 160000,
  "currency": "ZAR",
  "reference": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {...}
}
INFO Paystack initialize response: {
  "status": true,
  "message": "Authorization URL created",
  "data": {...}
}
```

**Verify Payment:**
```
INFO Processing Paystack callback for reference: paystack_reference_xxxx
INFO Paystack verify response: {
  "status": true,
  "data": {
    "status": "success",
    "amount": 160000,
    "currency": "ZAR",
    ...
  }
}
INFO Order 550e8400-e29b-41d4-a716-446655440000 marked as paid
```

---

## Frontend Integration

### Example: Initialize Payment

```typescript
// frontend/src/api.ts
export const initializePayment = async (bookingId: number, email: string, callbackUrl: string) => {
  const response = await fetch('/api/paystack/initialize-payment/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      booking_id: bookingId,
      email: email,
      callback_url: callbackUrl,
    }),
  });
  return response.json();
};
```

### Example: React Hook

```typescript
// frontend/src/hooks/usePayment.ts
export const usePayment = () => {
  const navigate = useNavigate();

  const processPayment = async (bookingId: number, email: string) => {
    const callbackUrl = `${window.location.origin}/payment-callback`;
    
    const result = await initializePayment(bookingId, email, callbackUrl);
    if (result.data?.authorization_url) {
      // Redirect to Paystack checkout
      window.location.href = result.data.authorization_url;
    }
  };

  return { processPayment };
};
```

### Example: Component

```typescript
// frontend/src/components/PaymentButton.tsx
export const PaymentButton: React.FC<{ bookingId: number; email: string }> = (props) => {
  const { processPayment } = usePayment();

  return (
    <button onClick={() => processPayment(props.bookingId, props.email)}>
      Proceed to Paystack
    </button>
  );
};
```

---

## Testing

### Test Mode

All keys use Paystack **test mode** (sk_test_*, pk_test_*). Use test card numbers:

**Successful Payment:**
```
Card Number: 4084084084084081
Expiry: 12/25 (or any future date)
CVV: 123
```

**Failed Payment:**
```
Card Number: 5555555555554444
Expiry: 12/25
CVV: 123
```

### Manual Testing (cURL)

**Initialize Payment:**
```bash
curl -X POST http://localhost:8000/api/paystack/initialize-payment/ \
  -H "Content-Type: application/json" \
  -d '{
    "booking_id": 1,
    "email": "test@example.com",
    "callback_url": "http://localhost:3000/payment-callback"
  }'
```

**Get Confirmation:**
```bash
curl http://localhost:8000/api/paystack/confirmation/550e8400-e29b-41d4-a716-446655440000/
```

**List Orders:**
```bash
curl http://localhost:8000/api/paystack/orders/?status=paid
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Missing required fields` | Missing booking_id, email, or callback_url | Verify payload |
| `Booking not found` | Invalid booking_id | Check booking exists |
| `Payment initialization failed` | Paystack API error | Check logs, verify keys |
| `Service error` (503) | Paystack API unreachable | Retry, check Paystack status |
| `Order not found` (callback) | Invalid reference | Verify reference parameter |

### Debugging Steps

1. **Check .env:** Ensure PAYSTACK_SECRET_KEY and PAYSTACK_PUBLIC_KEY are set
2. **Review logs:** Check `logs/paystack.log` for API requests/responses
3. **Verify keys:** Test keys on [Paystack Dashboard](https://dashboard.paystack.com/settings/developer)
4. **Network:** Ensure firewall allows outgoing HTTPS to `api.paystack.co`
5. **Database:** Verify Order records are created with `python manage.py dbshell`

---

## Production Deployment

### Before Going Live

1. **Update Keys:**
   ```env
   PAYSTACK_SECRET_KEY=sk_live_xxxxxxxxxxxxx  # Live secret key
   PAYSTACK_PUBLIC_KEY=pk_live_xxxxxxxxxxxxx  # Live public key
   ```

2. **Enable HTTPS:**
   ```python
   # settings.py
   DEBUG = False
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   ```

3. **Configure Allowed Hosts:**
   ```python
   ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
   ```

4. **Set Callback URL in Paystack Dashboard:**
   ```
   https://yourdomain.com/api/paystack/callback/
   ```

5. **Test Live Keys:**
   - Use live card numbers (provided by Paystack)
   - Process test transaction
   - Verify in Paystack Dashboard

---

## File Structure

```
paystack/
├── __init__.py
├── apps.py           # App configuration
├── admin.py          # Admin panel setup
├── models.py         # Order model
├── serializers.py    # Order serializer
├── views.py          # Payment views (initialize, callback, confirmation, list)
├── urls.py           # URL routes
├── tests.py          # Unit tests
└── migrations/
    └── 0001_initial.py  # Order model migration
```

---

## Support & Resources

- [Paystack Documentation](https://paystack.com/docs/payments/)
- [Paystack API Reference](https://paystack.com/docs/api/)
- [Test Card Numbers](https://paystack.com/docs/payments/test-bank-accounts-and-cards/)
- [Django REST Framework](https://www.django-rest-framework.org/)

---

## Summary

The Paystack integration provides:
- ✅ Secure redirect checkout for lodge bookings
- ✅ Automatic transaction verification
- ✅ Order tracking with status (pending/paid/failed/cancelled)
- ✅ Detailed logging for debugging
- ✅ Admin interface for viewing orders
- ✅ Environment-based configuration (test/live)

All payments are processed through Paystack's secure infrastructure. The backend handles initialization, verification, and confirmation without storing sensitive card data.
