# 🔗 Frontend-Backend Integration Guide
## Ikhaya Lami Lodge — Paystack Payment Integration

**Last Updated:** December 19, 2025  
**Backend API Base URL:** `http://localhost:8000` (dev) | `https://yourdomain.com` (prod)

---

## 📋 Table of Contents
1. [Payment Flow Overview](#payment-flow-overview)
2. [API Endpoints](#api-endpoints)
3. [Request/Response Formats](#requestresponse-formats)
4. [Integration Steps](#integration-steps)
5. [Error Handling](#error-handling)
6. [Code Examples](#code-examples)
7. [Testing Checklist](#testing-checklist)

---

## 🔄 Payment Flow Overview

```
Frontend (Reservation Form)
    ↓
POST /api/payments/initialize/
    ↓
Backend (Create Booking + Order, call Paystack API)
    ↓
Return: { authorization_url, reference }
    ↓
Frontend: window.location.href = authorization_url
    ↓
Paystack Checkout (Secure Payment Page)
    ↓
User Completes Payment
    ↓
Paystack Redirects: GET /api/paystack/callback/?reference=xxx
    ↓
Backend (Verify Payment with Paystack)
    ↓
Update Order.status = 'paid'
    ↓
Redirect: GET /api/paystack/booking-confirmation/<order_id>/
    ↓
Frontend (Show Confirmation Page)
```

---

## 🌐 API Endpoints

### 1. **Initialize Payment** (POST)
**Route:** `POST /api/payments/initialize/`

**Purpose:** Start a payment transaction for a booking.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "type": "chalet",                    // Required: "chalet", "campsite", "conference", "event", "safari"
  "name": "Jimmy Carter",              // Required: Customer name
  "email": "jimmy@carter.com",         // Required: Customer email (used in Paystack payload)
  "phone": "0123456789",               // Required: Customer phone number
  "check_in": "2025-12-03",            // Required: ISO date (YYYY-MM-DD)
  "check_out": "2025-12-05",           // Required: ISO date (YYYY-MM-DD) - must be after check_in
  "guests": 2,                         // Required: Integer ≥ 1
  "safari_slot": "morning",            // Optional: Only for type="safari" (morning|midday|afternoon)
  "message": "No special requests",    // Optional: Special instructions
  "callback_url": "http://localhost:3000/payment-callback/"  // Optional: Where Paystack redirects (defaults to backend callback)
}
```

**Response (201 Created):**
```json
{
  "message": "Payment initialized",
  "authorization_url": "https://checkout.paystack.com/xyzabc123",
  "reference": "uuid-based-order-reference"
}
```

**Response (400 Bad Request) - Missing Required Fields:**
```json
{
  "message": "email is required"
}
```

**Response (400 Bad Request) - Invalid Booking Data:**
```json
{
  "message": "Invalid booking data",
  "errors": {
    "check_in": ["Check-in date cannot be in the past."],
    "guests": ["'chalet' bookings must have between 1 and 4 guests."]
  }
}
```

**Response (503 Service Unavailable) - Paystack API Error:**
```json
{
  "message": "Payment service error"
}
```

---

### 2. **Paystack Callback** (GET)
**Route:** `GET /api/paystack/callback/?reference=<reference>`

**Purpose:** Verify payment with Paystack and update order status.

**Query Parameters:**
```
reference=uuid-based-order-reference  // Required: From initialize response
```

**Behavior:**
- Backend calls Paystack `/transaction/verify/{reference}` to confirm payment
- If successful: Updates `Order.status = 'paid'` → Redirects to booking confirmation
- If failed: Updates `Order.status = 'failed'` → Redirects to error page
- If not found: Returns error

**Redirects To:**
- **Success:** `GET /api/paystack/booking-confirmation/<order_id>/`
- **Failure:** `/payment-failed/?reference=<reference>`

---

### 3. **Booking Confirmation** (GET)
**Route:** `GET /api/paystack/booking-confirmation/<order_id>/`

**Purpose:** Display booking confirmation page (only if payment verified).

**Query Parameters:** None

**Response (200 OK) - If Order.status = 'paid':**
```html
<!doctype html>
<html>
<head><title>Booking Confirmation</title></head>
<body>
  <h1>Booking Confirmed</h1>
  <p>Order: abc-123-def</p>
  <p>Payment Reference: abc-123-def</p>
  <p>Amount Paid: 1600 ZAR</p>
  <h2>Booking Details</h2>
  <p>Confirmation Number: ABC123XYZ</p>
  <p>Type: chalet</p>
  <p>Check-in: 2025-12-03</p>
  <p>Check-out: 2025-12-05</p>
  <p>Guests: 2</p>
</body>
</html>
```

**Response (HTML) - If Order.status ≠ 'paid':**
```html
<p>Payment not completed for this booking.</p>
```

---

## 📦 Request/Response Formats

### Valid Booking Types
```javascript
const BOOKING_TYPES = {
  'chalet': 'Chalet (1-4 guests)',
  'campsite': 'Campsite (1-7 guests)',
  'conference': 'Conference (1-11 guests)',
  'event': 'Event (1-∞ guests)',
  'safari': 'Safari Drive (7-10 guests, requires safari_slot)'
};
```

### Safari Slots (Required for type='safari')
```javascript
const SAFARI_SLOTS = {
  'morning': 'Morning (07:30-09:30)',
  'midday': 'Midday (11:00-13:00)',
  'afternoon': 'Afternoon (15:30-17:30)'
};
```

### Pricing Per Night/Unit
```javascript
const PRICING = {
  'chalet': 800.00,      // ZAR per night
  'campsite': 200.00,    // ZAR per night
  'conference': 5000.00, // ZAR per booking
  'event': 1000.00,      // ZAR per booking
  'safari': 2500.00      // ZAR per booking
};
```

**Amount Calculation:**
- **Chalet/Campsite:** `base_price * (checkout_date - checkin_date).days`
- **Conference/Event/Safari:** `base_price` (flat rate)

**Example:** Chalet for 2 nights (12/03 - 12/05):
```
Amount = 800 * 2 = 1600 ZAR
Paystack receives: 1600 * 100 = 160000 (in cents/kobo)
```

---

## 🛠️ Integration Steps

### Step 1: Update Your Reservation Form
In your form component, capture these fields:
- `type` (dropdown)
- `name` (text input)
- `email` (email input)
- `phone` (tel input)
- `check_in` (date input)
- `check_out` (date input)
- `guests` (number input)
- `safari_slot` (conditional: show only if type='safari')
- `message` (textarea)

### Step 2: On Form Submit
Prevent default form submission and call the backend:

```javascript
async function handleSubmitReservation(formData) {
  // Build payload from form
  const payload = {
    type: formData.bookingType,
    name: formData.name,
    email: formData.email,
    phone: formData.phone,
    check_in: formData.checkInDate,
    check_out: formData.checkOutDate,
    guests: parseInt(formData.numGuests),
    safari_slot: formData.safariSlot || undefined,
    message: formData.message || "",
    callback_url: `${window.location.origin}/payment-callback/`
  };

  try {
    const response = await fetch('http://localhost:8000/api/payments/initialize/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const error = await response.json();
      console.error('Initialize failed:', error);
      showErrorToUser(error.message || 'Payment initialization failed');
      return;
    }

    const data = await response.json();
    console.log('Payment initialized:', data);

    // Redirect to Paystack checkout
    window.location.href = data.authorization_url;

  } catch (error) {
    console.error('Network error:', error);
    showErrorToUser('Network error. Please try again.');
  }
}
```

### Step 3: Create Callback Handler
Your frontend should handle the redirect from Paystack:

```javascript
// Page: /payment-callback/ or similar
function PaymentCallbackPage() {
  useEffect(() => {
    // Backend redirects here after Paystack callback
    // Show a loading message while being redirected to confirmation
    return <div>Processing payment...</div>;
  }, []);
}
```

### Step 4: Confirmation Page
Display the booking confirmation (backend renders HTML automatically at `/api/paystack/booking-confirmation/<order_id>/`):

```javascript
// After successful payment, user lands on:
// GET /api/paystack/booking-confirmation/<order_id>/
// Backend returns HTML with booking details
```

---

## ⚠️ Error Handling

### Frontend Should Handle These Status Codes:

| Status | Meaning | Action |
|--------|---------|--------|
| 201 | Payment initialized successfully | Redirect to `authorization_url` |
| 400 | Invalid request (missing/bad data) | Show error message + validation hints |
| 404 | Booking/Order not found | Retry or contact support |
| 503 | Paystack API unreachable | Show "Service unavailable" message |
| 500 | Unexpected server error | Show generic error + log to backend |

### Common Error Messages:
```json
{
  "message": "email is required"
}

{
  "message": "Invalid booking data",
  "errors": {
    "check_in": ["Check-in date cannot be in the past."],
    "guests": ["'chalet' bookings must have between 1 and 4 guests."]
  }
}

{
  "message": "Booking not found"
}

{
  "message": "Payment service error"
}
```

---

## 💻 Code Examples

### React Integration Example

```jsx
import React, { useState } from 'react';

function ReservationForm() {
  const [formData, setFormData] = useState({
    type: 'chalet',
    name: '',
    email: '',
    phone: '',
    checkInDate: '',
    checkOutDate: '',
    numGuests: 1,
    safariSlot: '',
    message: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload = {
      type: formData.type,
      name: formData.name,
      email: formData.email,
      phone: formData.phone,
      check_in: formData.checkInDate,
      check_out: formData.checkOutDate,
      guests: parseInt(formData.numGuests),
      safari_slot: formData.safariSlot || undefined,
      message: formData.message || "",
      callback_url: `${window.location.origin}/payment-callback/`
    };

    try {
      const response = await fetch('http://localhost:8000/api/payments/initialize/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Payment initialization failed');
      }

      const data = await response.json();
      console.log('Redirecting to Paystack:', data.authorization_url);
      window.location.href = data.authorization_url;

    } catch (err) {
      console.error('Error:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>Full Name:</label>
        <input 
          type="text" 
          name="name" 
          value={formData.name}
          onChange={handleChange}
          required 
        />
      </div>

      <div>
        <label>Email:</label>
        <input 
          type="email" 
          name="email" 
          value={formData.email}
          onChange={handleChange}
          required 
        />
      </div>

      <div>
        <label>Phone Number:</label>
        <input 
          type="tel" 
          name="phone" 
          value={formData.phone}
          onChange={handleChange}
          required 
        />
      </div>

      <div>
        <label>Booking Type:</label>
        <select name="type" value={formData.type} onChange={handleChange}>
          <option value="chalet">Chalet (1-4 guests)</option>
          <option value="campsite">Campsite (1-7 guests)</option>
          <option value="conference">Conference (1-11 guests)</option>
          <option value="event">Event</option>
          <option value="safari">Safari Drive (7-10 guests)</option>
        </select>
      </div>

      {formData.type === 'safari' && (
        <div>
          <label>Safari Time Slot:</label>
          <select name="safariSlot" value={formData.safariSlot} onChange={handleChange} required>
            <option value="">Select a slot</option>
            <option value="morning">Morning (07:30-09:30)</option>
            <option value="midday">Midday (11:00-13:00)</option>
            <option value="afternoon">Afternoon (15:30-17:30)</option>
          </select>
        </div>
      )}

      <div>
        <label>Check-in Date:</label>
        <input 
          type="date" 
          name="checkInDate" 
          value={formData.checkInDate}
          onChange={handleChange}
          required 
        />
      </div>

      <div>
        <label>Check-out Date:</label>
        <input 
          type="date" 
          name="checkOutDate" 
          value={formData.checkOutDate}
          onChange={handleChange}
          required 
        />
      </div>

      <div>
        <label>Number of Guests:</label>
        <input 
          type="number" 
          name="numGuests" 
          value={formData.numGuests}
          onChange={handleChange}
          min="1"
          required 
        />
      </div>

      <div>
        <label>Message (Optional):</label>
        <textarea 
          name="message" 
          value={formData.message}
          onChange={handleChange}
        />
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      <button type="submit" disabled={loading}>
        {loading ? 'Processing...' : 'Proceed to Secure Payment'}
      </button>
    </form>
  );
}

export default ReservationForm;
```

### Vanilla JavaScript Example

```javascript
function initializePayment(formElement) {
  formElement.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(formElement);
    const payload = {
      type: formData.get('bookingType'),
      name: formData.get('name'),
      email: formData.get('email'),
      phone: formData.get('phone'),
      check_in: formData.get('checkInDate'),
      check_out: formData.get('checkOutDate'),
      guests: parseInt(formData.get('numGuests')),
      safari_slot: formData.get('safariSlot') || undefined,
      message: formData.get('message') || "",
      callback_url: `${window.location.origin}/payment-callback/`
    };

    try {
      const response = await fetch('http://localhost:8000/api/payments/initialize/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const error = await response.json();
        alert('Payment Error: ' + (error.message || 'Unknown error'));
        return;
      }

      const data = await response.json();
      window.location.href = data.authorization_url;

    } catch (error) {
      alert('Network Error: ' + error.message);
    }
  });
}

// Usage:
// initializePayment(document.getElementById('reservationForm'));
```

---

## ✅ Testing Checklist

### Unit Tests (Frontend)
- [ ] Form validation: All required fields present before submit
- [ ] Date validation: check_out > check_in
- [ ] Safari slot: Required only when type='safari'
- [ ] Payload structure matches API specification

### Integration Tests
- [ ] POST to `/api/payments/initialize/` returns 201 with `authorization_url`
- [ ] Redirect to `authorization_url` works (manual test with Paystack test card)
- [ ] Paystack callback redirects to `/api/paystack/booking-confirmation/<order_id>/`
- [ ] Confirmation page displays booking details

### Paystack Test Card
```
Card Number:      4084 0840 8408 4081
Expiry:           12/25
CVV:              123
OTP (if prompted): 123456
```

### Manual Testing Steps
1. Fill reservation form with valid data
2. Click "Submit Booking"
3. Redirected to Paystack checkout
4. Enter test card details (above)
5. Complete payment
6. Redirected to confirmation page
7. Verify booking details match submission

### Error Testing
- [ ] Omit required field → 400 error message displayed
- [ ] Invalid check_in date (past) → Validation error shown
- [ ] Exceed guest limit for booking type → Error message shown

---

## 🔐 Security Notes

1. **CORS:** Backend allows all origins in dev (`CORS_ALLOW_ALL_ORIGINS = True`). Change in production.
2. **HTTPS:** Paystack redirect uses HTTPS. Ensure frontend is also HTTPS in production.
3. **API Keys:** Backend stores `PAYSTACK_SECRET_KEY` in `.env` (never exposed to frontend).
4. **CSRF:** Backend exempts `/api/payments/initialize/` for cross-origin POST.

---

## 📞 Support / Debugging

### Backend Logs
Check `logs/paystack.log` for:
- Incoming request payloads
- Customer email address used
- Paystack API responses
- Order status updates

### Common Issues

**Q: Getting 403 Forbidden**  
A: Backend CSRF protection. Ensure `Content-Type: application/json` header is sent.

**Q: Getting 404 Not Found**  
A: Endpoint is `/api/payments/initialize/` not `/api/paystack/initialize/`.

**Q: Paystack redirect failing**  
A: Verify `PAYSTACK_PUBLIC_KEY` and `PAYSTACK_SECRET_KEY` in backend `.env`.

**Q: Callback not updating order status**  
A: Check backend logs for Paystack verify errors. Ensure `reference` is passed correctly.

---

## 📚 Resources

- **Paystack Docs:** https://paystack.com/docs/
- **Backend API Logs:** `logs/paystack.log`
- **Backend Settings:** `lodge_backend/settings.py`
- **Booking Model:** `bookings/models.py`
- **Payment Order Model:** `paystack/models.py`

---

**Backend Ready:** ✅  
**Frontend Integration:** 🚀 Ready to implement
