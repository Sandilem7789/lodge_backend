# Lodge Backend Server Blueprint

**Project:** Django REST Framework API for lodge booking management  
**Database:** SQLite (development)  
**Python Version:** 3.13  
**Framework:** Django 5.2, Django REST Framework

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Database Models](#database-models)
3. [API Endpoints](#api-endpoints)
4. [Serializers & Validation](#serializers--validation)
5. [Views & Business Logic](#views--business-logic)
6. [Capacity & Availability Rules](#capacity--availability-rules)
7. [Authentication & Permissions](#authentication--permissions)
8. [URL Routing](#url-routing)
9. [Payment Integration (Paystack)](#payment-integration-paystack)
10. [Frontend Integration](#frontend-integration)
11. [Testing & Development](#testing--development)

---

## Project Structure

```
lodge_backend/
├── manage.py
├── db.sqlite3
├── lodge_backend/                 # Project settings
│   ├── settings.py               # Django config, installed apps, middleware
│   ├── urls.py                   # Project-level URL routing
│   ├── asgi.py
│   ├── wsgi.py
│   └── __pycache__/
├── bookings/                      # Core booking app
│   ├── models.py                 # Booking, related models
│   ├── serializers.py            # BookingSerializer, AvailabilitySerializer
│   ├── views.py                  # All booking views & staff dashboard
│   ├── urls.py                   # Booking endpoint routes
│   ├── admin.py
│   ├── apps.py
│   ├── tests.py
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   ├── 0002_booking_status.py
│   │   ├── 0003_cancellation_fields.py
│   │   ├── 0004_booking_safari_slot.py
│   │   └── __init__.py
│   └── templates/
│       └── bookings/
│           └── staff_dashboard.html
├── contact/                       # Contact forms & booking requests
│   ├── models.py                 # ContactMessage, BookingRequest
│   ├── serializers.py            # Serializers
│   ├── views.py                  # Create & list views
│   ├── urls.py                   # Routes
│   ├── admin.py
│   ├── apps.py
│   ├── tests.py
│   └── migrations/
├── newsletter/                    # Newsletter subscriptions
│   ├── models.py                 # Subscriber
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── apps.py
│   ├── tests.py
│   └── migrations/
├── paystack/                      # Payment processing
│   ├── models.py                 # Order model
│   ├── serializers.py            # Order serializer
│   ├── views.py                  # Payment views
│   ├── urls.py                   # Payment routes
│   ├── admin.py
│   ├── apps.py
│   ├── tests.py
│   └── migrations/
├── logs/                          # Logging directory
│   ├── django.log                # General logs
│   └── paystack.log              # Payment logs
└── frontend/
    └── src/
        ├── api.ts                # API helper with naming conversion
        ├── hooks/
        │   └── useBookings.ts    # React hook example
        └── components/
            └── BookingForm.tsx   # Example React component
```

---

## Database Models

### 1. **Booking** (bookings/models.py)

Core model for all facility reservations.

```python
class Booking(models.Model):
    BOOKING_TYPES = [
        ('chalet', 'Chalet'),
        ('campsite', 'Campsite'),
        ('conference', 'Conference'),
        ('event', 'Event'),
        ('safari', 'Safari'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    
    SAFARI_SLOTS = [
        ('morning', 'Morning (08:00-11:00)'),
        ('midday', 'Midday (12:00-15:00)'),
        ('afternoon', 'Afternoon (16:00-19:00)'),
    ]
    
    # Fields
    type: CharField (choices: chalet, campsite, conference, event, safari)
    name: CharField (guest name)
    email: EmailField
    phone: CharField
    check_in: DateField
    check_out: DateField (not required for safari, only check_in used)
    guests: IntegerField (number of guests)
    safari_slot: CharField (for safari bookings: morning, midday, afternoon)
    message: TextField (optional notes)
    status: CharField (default='confirmed', choices: pending, confirmed, cancelled)
    cancelled_at: DateTimeField (null=True, set when cancelled)
    cancellation_reason: TextField (optional reason for cancellation)
    confirmation_number: CharField (unique, auto-generated UUID)
    created_at: DateTimeField (auto_now_add=True)
```

**Key methods:**
- `__str__()` — returns `f"{confirmation_number} - {type} ({name})"`

---

### 2. **BookingRequest** (contact/models.py)

Stores public booking enquiries (contact form submissions for booking).

```python
class BookingRequest(models.Model):
    name: CharField
    email: EmailField
    phone: CharField
    type: CharField (choices: chalet, campsite, conference, event, safari)
    check_in: DateField
    check_out: DateField (null=True, blank=True)
    guests: IntegerField
    message: TextField
    created_at: DateTimeField (auto_now_add=True)
```

---

### 3. **ContactMessage** (contact/models.py)

General contact form submissions.

```python
class ContactMessage(models.Model):
    name: CharField
    email: EmailField
    subject: CharField
    message: TextField
    created_at: DateTimeField (auto_now_add=True)
```

---

### 4. **Subscriber** (newsletter/models.py)

Email subscribers.

```python
class Subscriber(models.Model):
    email: EmailField (unique)
    subscribed_at: DateTimeField (auto_now_add=True)
```

---

### 5. **Order** (paystack/models.py)

Payment transaction records linked to bookings.

```python
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_id: CharField (unique, auto-generated UUID)
    booking: OneToOneField (ForeignKey to Booking)
    amount: DecimalField (in ZAR)
    currency: CharField (default='ZAR')
    status: CharField (default='pending', choices: pending, paid, failed, cancelled)
    reference: CharField (Paystack transaction reference, unique)
    email: EmailField (customer email for payment)
    created_at: DateTimeField (auto_now_add=True)
    updated_at: DateTimeField (auto_now=True)
```

**Key methods:**
- `__str__()` — returns `f"Order {order_id} - {status} (ZAR {amount})"`

---

## API Endpoints

### Bookings App (`/api/bookings/`)

| Method | Endpoint | Description | Auth | Returns |
|--------|----------|-------------|------|---------|
| GET | `/api/bookings/` | List all bookings (with filters) | Public | Array of bookings |
| POST | `/api/bookings/` | Create new booking | Public | Booking with confirmation_number |
| GET | `/api/bookings/<confirmation_number>/` | Retrieve booking by confirmation # | Public | Single booking |
| DELETE | `/api/bookings/<confirmation_number>/` | Delete booking | Public | Success message |
| PATCH | `/api/bookings/<confirmation_number>/cancel/` | Cancel booking | Public | Booking with status='cancelled' |
| GET | `/api/bookings/grouped/` | Bookings grouped by type with counts | Public | Counts per type or list for specific type |
| GET | `/api/availability/` | Fully-booked dates per type | Public | Dates per type (date range defaults to 30 days) |
| GET | `/api/safari-availability/?date=YYYY-MM-DD` | Per-slot booked guest counts | Public | `{date: {morning: N, midday: N, afternoon: N}}` |

#### Query Parameters

**List bookings** (`GET /api/bookings/`):
- `start_date` (YYYY-MM-DD) — filter check_in >= date
- `end_date` (YYYY-MM-DD) — filter check_out <= date
- `status` (pending|confirmed|cancelled) — filter by status
- `name` (string) — filter by guest name (partial match)
- `search` (string) — search name, email, or confirmation_number

**Grouped bookings** (`GET /api/bookings/grouped/`):
- `type` (optional) — if provided, returns detailed list for that type; otherwise returns counts
- (all above filters apply)

**Availability calendar** (`GET /api/availability/`):
- `start_date` (default: today)
- `end_date` (default: today + 30 days)

---

### Payment App - Paystack (`/api/paystack/`)

| Method | Endpoint | Description | Auth | Returns |
|--------|----------|-------------|------|---------|
| POST | `/api/paystack/initialize-payment/` | Initialize payment transaction | Public | Order with authorization_url |
| GET | `/api/paystack/callback/?reference=...` | Verify payment (called by Paystack) | Public | Redirect to confirmation/failure |
| GET | `/api/paystack/confirmation/<order_id>/` | Get payment confirmation details | Public | Order + booking details |
| GET | `/api/paystack/orders/` | List all payment orders | Admin | Array of orders |

---

### Contact App (`/api/contact/`)

| Method | Endpoint | Description | Auth | Returns |
|--------|----------|-------------|------|---------|
| POST | `/api/contact/submit/` | Submit contact form | Public | Success message |
| GET | `/api/contact/booking-requests/` | (Not directly; see BookingRequest) | — | — |
| POST | `/api/contact/booking-requests/` | Submit booking enquiry | Public | BookingRequest with ID |
| GET | `/api/contact/booking-requests/list/` | List booking requests | Staff only | Array of requests |

---

### Newsletter App (`/api/newsletter/`)

| Method | Endpoint | Description | Auth | Returns |
|--------|----------|-------------|------|---------|
| POST | `/api/newsletter/subscribe/` | Subscribe email to newsletter | Public | Success message |

---

### Staff Dashboard

| Method | Endpoint | Description | Auth | Template |
|--------|----------|-------------|------|----------|
| GET | `/staff-area-9f3b7d3a-portal/` | Staff-only dashboard | Staff login required | `bookings/staff_dashboard.html` |

**Context variables:**
- `recent_bookings` — last 25 bookings (order by created_at desc)
- `counts_by_type` — dict of type → count
- `cancelled_count` — total cancelled bookings
- `recent_booking_requests` — last 25 booking requests

---

## Serializers & Validation

### BookingSerializer (bookings/serializers.py)

**Fields (read/write):**
```python
type, name, email, phone, check_in, check_out, guests, safari_slot, message, status, 
cancelled_at, cancellation_reason, confirmation_number (read-only), created_at (read-only)
```

**Validations:**
1. **Email & Phone:** Required.
2. **Dates:** `check_in < check_out`, check_in not in past.
3. **Guests:** ≥ 1.
4. **Type-specific guest limits:**
   - Chalet: 1–4 guests
   - Campsite: 1–7 guests
   - Conference: 1–11 guests
   - Safari: 7–10 guests (required)
   - Event: 1–9999 guests

5. **Safari-specific:**
   - Requires `safari_slot` (morning|midday|afternoon).
   - Requires `check_in` (used as date; check_out ignored).
   - Per-slot daily capacity: Sum of existing guests (same slot, same check_in, non-cancelled) + new guests ≤ 30.
   - Error if exceeded: `"Selected time slot is fully booked"`.

6. **Non-safari bookings:**
   - Validate per-date unit availability:
     - Chalet: max 3 overlapping units per night.
     - Campsite: max 10 overlapping units per night.
     - Conference: max 1 overlapping unit per night.
     - Event: unlimited.

**Create behavior:**
- Auto-generates `confirmation_number` as UUID (12 chars uppercase).
- Defaults `status` to 'confirmed'.

---

### AvailabilitySerializer (bookings/serializers.py)

Input validation for availability checks.

**Fields:**
```python
type (required), check_in (required), check_out (required)
```

**Validations:**
- `check_in < check_out`
- `check_in` not in past

---

### BookingRequestSerializer (contact/serializers.py)

**Fields:**
```python
name, email, phone, type, check_in, check_out (nullable), guests, message, created_at (read-only)
```

---

### ContactMessageSerializer (contact/serializers.py)

**Fields:**
```python
name, email, subject, message, created_at (read-only)
```

---

### SubscriberSerializer (newsletter/serializers.py)

**Fields:**
```python
email (unique), subscribed_at (read-only)
```

---

## Views & Business Logic

### BookingCreateView (APIView)

**POST /api/bookings/**
- Accepts JSON payload (booking data).
- Validates via `BookingSerializer`.
- On success: returns `{ message, data }` with HTTP 201.
- On error: returns `{ message, errors }` with HTTP 400.

---

### BookingListCreateView (APIView)

**GET /api/bookings/**
- Lists all bookings with optional filters (start_date, end_date, status, name, search).
- Returns `{ message, count, data }` with HTTP 200.

**POST /api/bookings/**
- Same as `BookingCreateView`.

---

### BookingDetailView (APIView)

**GET /api/bookings/<confirmation_number>/**
- Retrieves single booking.
- Returns `{ message, data }` or 404.

**DELETE /api/bookings/<confirmation_number>/**
- Deletes booking from DB.
- Returns `{ message }` with HTTP 200.

---

### BookingCancelView (APIView)

**PATCH /api/bookings/<confirmation_number>/cancel/**
- Updates `status='cancelled'`, sets `cancelled_at=now()`.
- Optional `cancellation_reason` in request body.
- Returns serialized booking with HTTP 200.

---

### GroupedBookingsView (APIView)

**GET /api/bookings/grouped/**
- If `type` query param: returns detailed list for that type.
- Otherwise: returns counts per type + total.
- Applies same filters as list view.

---

### AvailabilityCalendarView (APIView)

**GET /api/availability/?start_date=...&end_date=...**
- Returns fully-booked dates per type for date range.
- Response:
  ```json
  {
    "chalet": ["2025-12-20", "2025-12-21"],
    "campsite": [],
    "conference": ["2025-12-25"],
    "event": [],
    "safari": ["2025-12-11"],
    "total": 4
  }
  ```
- Default range: today to today + 30 days.

---

### SafariAvailabilityView (APIView)

**GET /api/safari-availability/?date=YYYY-MM-DD**
- Returns per-slot booked guest counts for a single date.
- Response:
  ```json
  {
    "2025-12-11": {
      "morning": 15,
      "midday": 20,
      "afternoon": 10
    }
  }
  ```
- Uses `Sum('guests')` to aggregate non-cancelled bookings per slot/date.

---

### StaffDashboardView (TemplateView)

**GET /staff-area-9f3b7d3a-portal/**
- Protected: requires login + `user.is_staff == True`.
- Renders `bookings/staff_dashboard.html` with context:
  - Recent bookings, type counts, cancelled count, recent booking requests.
- Purpose: quick operational overview for staff.

---

### Contact Views

**BookingRequestCreateView (APIView)** — POST `/api/contact/booking-requests/`
- Accepts booking enquiry (name, email, phone, type, check_in, check_out, guests, message).
- Stores in `BookingRequest` model.
- Returns success message.

**BookingRequestListView (APIView)** — GET `/api/contact/booking-requests/list/`
- Staff-only (protected by `user_passes_test(lambda u: u.is_staff)`).
- Lists all booking requests.

---

## Capacity & Availability Rules

### Capacity Configuration

Defined in `BookingSerializer.validate()`:

```python
capacity = {
    'chalet': {'units': 3, 'min': 1, 'max': 4},
    'campsite': {'units': 10, 'min': 1, 'max': 7},
    'conference': {'units': 1, 'min': 1, 'max': 11},
    'safari': {'units': 3, 'min': 7, 'max': 10, 'daily_max': 30},
    'event': {'units': 9999, 'min': 1, 'max': 9999},
}
```

### Non-Safari Logic

For chalet, campsite, conference:
- Check each night (check_in to check_out-1).
- Count overlapping bookings (status != 'cancelled') where `check_in ≤ night < check_out`.
- If count ≥ units: reject with "Fully booked" error.

### Safari Logic

For safari bookings:
- Require `safari_slot` (morning|midday|afternoon).
- Sum guests for (type='safari', safari_slot=X, check_in=date, status != 'cancelled').
- If sum + new guests > 30: reject with "Selected time slot is fully booked".

---

## Authentication & Permissions

### Public Endpoints
All booking, contact, newsletter endpoints are public (no token required).

### Protected Endpoints
- **Staff Dashboard** (`/staff-area-9f3b7d3a-portal/`):
  - Requires Django login (`login_required`).
  - Requires `user.is_staff == True`.
- **Booking Request List** (`/api/contact/booking-requests/list/`):
  - Requires `user.is_staff == True`.

### Security Notes
- Staff dashboard placed at non-obvious URL to reduce enumeration risk.
- No API token auth implemented (public API for now).
- Consider adding CORS restrictions, rate limiting, and HTTPS in production.
- Settings recommend secure cookies & HSTS when `DEBUG=False`.

---

## URL Routing

### Project-Level (`lodge_backend/urls.py`)

```python
path('admin/', admin.site.urls),
path('staff-area-9f3b7d3a-portal/', StaffDashboardView.as_view(), name='staff-dashboard'),
path('api/availability/', AvailabilityCalendarView.as_view(), name='availability-calendar'),
path('api/safari-availability/', SafariAvailabilityView.as_view(), name='safari-availability'),
path('api/bookings/', include('bookings.urls')),
path('api/contact/', include('contact.urls')),
path('api/newsletter/', include('newsletter.urls')),
```

### Bookings App (`bookings/urls.py`)

```python
path('', BookingListCreateView.as_view(), name='booking-list-create'),           # GET/POST
path('availability/', AvailabilityCheckView.as_view(), name='availability'),     # GET
path('grouped/', GroupedBookingsView.as_view(), name='grouped'),                 # GET
path('<confirmation_number>/', BookingDetailView.as_view(), name='booking-detail'),  # GET/DELETE
path('<confirmation_number>/cancel/', BookingCancelView.as_view(), name='booking-cancel'),  # PATCH
```

### Paystack App (`paystack/urls.py`)

```python
path('initialize-payment/', InitializePaymentView.as_view(), name='initialize-payment'),  # POST
path('callback/', PaystackCallbackView.as_view(), name='callback'),  # GET (Paystack redirect)
path('confirmation/<str:order_id>/', PaymentConfirmationView.as_view(), name='confirmation'),  # GET
path('orders/', OrderListView.as_view(), name='orders-list'),  # GET
```

### Contact App (`contact/urls.py`)

```python
path('submit/', ContactMessageCreateView.as_view(), name='contact-submit'),
path('booking-requests/', BookingRequestCreateView.as_view(), name='booking-request-create'),
path('booking-requests/list/', BookingRequestListView.as_view(), name='booking-request-list'),
```

### Newsletter App (`newsletter/urls.py`)

```python
path('subscribe/', SubscriberCreateView.as_view(), name='subscribe'),
```

---

## Payment Integration (Paystack)

### Overview

Secure payment processing via Paystack redirect checkout. All keys loaded from `.env` using `python-decouple`.

### Configuration (settings.py)

```python
from decouple import config

PAYSTACK_SECRET_KEY = config('PAYSTACK_SECRET_KEY', default='')
PAYSTACK_PUBLIC_KEY = config('PAYSTACK_PUBLIC_KEY', default='')
PAYSTACK_CURRENCY = config('PAYSTACK_CURRENCY', default='ZAR')
```

### Environment Variables (.env)

```env
PAYSTACK_SECRET_KEY=sk_test_xxxxxxxxxxxxx
PAYSTACK_PUBLIC_KEY=pk_test_xxxxxxxxxxxxx
PAYSTACK_CURRENCY=ZAR
```

### Payment Flow

```
1. Customer → POST /api/paystack/initialize-payment/ (booking_id, email, callback_url)
2. Backend → Create Order (status: pending) + Call Paystack /transaction/initialize
3. Paystack → Return authorization_url (checkout page)
4. Frontend → Redirect customer to authorization_url
5. Customer → Fill payment details on Paystack
6. Paystack → Redirect to callback_url with ?reference=<paystack_reference>
7. Backend → GET /api/paystack/callback/ with reference
8. Backend → Call Paystack /transaction/verify/{reference}
9. Backend → Update Order.status (paid or failed)
10. Backend → Redirect to /payment-confirmation/ or /payment-failed/
```

### Views (paystack/views.py)

| View | Method | Purpose |
|------|--------|---------|
| InitializePaymentView | POST | Create Order + call Paystack initialize API |
| PaystackCallbackView | GET | Verify transaction + update Order status |
| PaymentConfirmationView | GET | Show payment confirmation details |
| OrderListView | GET | List all orders (admin) |

### Amount Calculation

Pricing per booking type:
- Chalet: 800 ZAR/night
- Campsite: 200 ZAR/night
- Conference: 5000 ZAR (flat)
- Safari: 2500 ZAR (flat)
- Event: 1000 ZAR (flat)

Customize in `InitializePaymentView._calculate_amount()`.

### Logging

- **General:** `logs/django.log`
- **Payments:** `logs/paystack.log`

Log levels: DEBUG (payloads), INFO (events), ERROR (failures)

### Error Handling

| Error | Solution |
|-------|----------|
| `Missing required fields` | Verify payload (booking_id, email, callback_url) |
| `Booking not found` | Check booking exists in database |
| `Payment initialization failed` | Check .env keys, Paystack API status |
| `Service error (503)` | Paystack API unreachable; retry later |

### Test Mode

Use Paystack **test keys** (`sk_test_*`, `pk_test_*`):

**Success Card:** `4084084084084081` / 12/25 / 123  
**Failed Card:** `5555555555554444` / 12/25 / 123

For production, update to live keys (`sk_live_*`, `pk_live_*`).

### See Also

Full guide: [PAYSTACK_INTEGRATION.md](PAYSTACK_INTEGRATION.md)

---

## Frontend Integration

### Naming Convention

**Backend (API):** snake_case
**Frontend (JS/TS):** camelCase

### Transformation Layer (`frontend/src/api.ts`)

Provides helpers to convert between naming conventions:

```typescript
// toSnake: camelCase → snake_case
// toCamel: snake_case → camelCase

const request = async (method, url, payload?) => {
  const snakePayload = toSnake(payload);
  const response = await fetch(url, { method, body: JSON.stringify(snakePayload) });
  return toCamel(await response.json());
};

export const createBooking = (data) => request('POST', '/api/bookings/', data);
export const getBookings = (filters) => request('GET', `/api/bookings/?${qs(filters)}`);
export const cancelBooking = (confirmationNumber, reason) => 
  request('PATCH', `/api/bookings/${confirmationNumber}/cancel/`, { cancellationReason: reason });
export const getSafariAvailability = (date) => 
  request('GET', `/api/safari-availability/?date=${date}`);
```

### Example React Hook (`frontend/src/hooks/useBookings.ts`)

Provides camelCase state and API methods:

```typescript
export const useBookings = () => {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchBookings = async (filters) => {
    setLoading(true);
    const data = await getBookings(filters);
    setBookings(data); // camelCase
    setLoading(false);
  };

  const create = async (booking) => {
    const result = await createBooking(booking);
    setBookings([...bookings, result]);
    return result;
  };

  return { bookings, loading, fetchBookings, create };
};
```

### Example Component (`frontend/src/components/BookingForm.tsx`)

React component using the hook:

```typescript
export const BookingForm: React.FC = () => {
  const { create } = useBookings();
  const [form, setForm] = useState({
    type: 'chalet',
    name: '',
    email: '',
    phone: '',
    checkIn: '',
    checkOut: '',
    guests: 1,
    safariSlot: 'morning',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await create(form);
    console.log('Booking created:', result.confirmationNumber);
  };

  return <form onSubmit={handleSubmit}>{ /* form fields */ }</form>;
};
```

---

## Testing & Development

### Running Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Running Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

### Testing Endpoints (Examples)

**Create a chalet booking:**
```bash
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "chalet",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "check_in": "2025-12-20",
    "check_out": "2025-12-25",
    "guests": 2,
    "message": "Ground floor preferred"
  }'
```

**Create a safari booking:**
```bash
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "safari",
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "+1234567891",
    "check_in": "2025-12-11",
    "guests": 8,
    "safari_slot": "morning"
  }'
```

**Check safari availability:**
```bash
curl http://localhost:8000/api/safari-availability/?date=2025-12-11
```

**List bookings with filters:**
```bash
curl 'http://localhost:8000/api/bookings/?status=confirmed&start_date=2025-12-10&end_date=2025-12-31'
```

**Cancel a booking:**
```bash
curl -X PATCH http://localhost:8000/api/bookings/ABC123XYZ/cancel/ \
  -H "Content-Type: application/json" \
  -d '{"cancellation_reason": "Guest requested"}'
```

---

## Summary

This backend provides a complete REST API for managing lodge bookings with:
- **Multi-type support** (chalet, campsite, conference, event, safari).
- **Capacity enforcement** per unit and per date.
- **Safari time slots** with daily capacity limits.
- **Booking lifecycle** (create, view, list, cancel, delete).
- **Availability calendar** showing fully-booked dates.
- **Contact & requests** management with staff dashboard.
- **Naming convention bridge** (snake_case API ↔ camelCase frontend).

All endpoints are public and stateless; staff-only views require Django authentication. Extend with token auth, rate limiting, and webhook notifications as needed.
