# Ikhaya Lami Lodge Backend API Documentation

## Overview
This Django REST Framework backend provides API endpoints for managing bookings, contact messages, and newsletter subscriptions for Ikhaya Lami Lodge.

## Setup Instructions

### 1. Install Dependencies
```bash
pip install django djangorestframework
```

### 2. Run Migrations
```bash
python manage.py migrate
```

### 3. Create Superuser (Optional, for admin access)
```bash
python manage.py createsuperuser
```

### 4. Run Development Server
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

---

## API Endpoints

### Bookings

#### 1. Create a Booking
**Endpoint:** `POST /api/bookings/`

**Request Body:**
```json
{
    "type": "chalet",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+27712345678",
    "check_in": "2025-12-20",
    "check_out": "2025-12-25",
    "guests": 4,
    "message": "Looking forward to our stay!"
}
```

**Response (201 Created):**
```json
{
    "message": "Booking created successfully.",
    "data": {
        "id": 1,
        "type": "chalet",
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+27712345678",
        "check_in": "2025-12-20",
        "check_out": "2025-12-25",
        "guests": 4,
        "message": "Looking forward to our stay!",
        "confirmation_number": "A7F3B2C8E5D1",
        "created_at": "2025-12-06T10:30:00Z"
    }
}
```

**Validation Rules:**
- `type`: Must be one of: `chalet`, `campsite`, `conference`, `event`, `safari`
- `name`: Required
- `email`: Required and must be valid email format
- `phone`: Required
- `check_in`: Must be before `check_out` and not in the past
- `guests`: Must be at least 1

---

#### 2. Check Availability
**Endpoint:** `GET /api/bookings/availability/?type=chalet&check_in=2025-12-20&check_out=2025-12-25`

**Query Parameters:**
- `type`: Required. One of: `chalet`, `campsite`, `conference`, `event`, `safari`
- `check_in`: Required. Date in format YYYY-MM-DD
- `check_out`: Required. Date in format YYYY-MM-DD

**Response (200 OK):**
```json
{
    "type": "chalet",
    "check_in": "2025-12-20",
    "check_out": "2025-12-25",
    "available": true,
    "conflicting_bookings_count": 0
}
```

**Response (400 Bad Request):**
```json
{
    "message": "Invalid query parameters.",
    "errors": {
        "check_in": ["Check-in date cannot be in the past."]
    }
}
```

---

#### 3. Retrieve Booking by Confirmation Number
**Endpoint:** `GET /api/bookings/<confirmationNumber>/`

**Example:** `GET /api/bookings/A7F3B2C8E5D1/`

**Response (200 OK):**
```json
{
    "message": "Booking retrieved successfully.",
    "data": {
        "id": 1,
        "type": "chalet",
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+27712345678",
        "check_in": "2025-12-20",
        "check_out": "2025-12-25",
        "guests": 4,
        "message": "Looking forward to our stay!",
        "confirmation_number": "A7F3B2C8E5D1",
        "created_at": "2025-12-06T10:30:00Z"
    }
}
```

**Response (404 Not Found):**
```json
{
    "message": "Booking not found."
}
```

---

### Contact Form

#### Submit Contact Message
**Endpoint:** `POST /api/contact/`

**Request Body:**
```json
{
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "+27712345678",
    "subject": "Inquiry about group bookings",
    "message": "I would like to inquire about group booking rates..."
}
```

**Response (201 Created):**
```json
{
    "message": "Contact message received successfully.",
    "data": {
        "id": 1,
        "name": "Jane Smith",
        "email": "jane@example.com",
        "created_at": "2025-12-06T10:35:00Z"
    }
}
```

**Validation Rules:**
- `name`: Required (non-empty string)
- `email`: Required and must be valid email format
- `phone`: Optional
- `subject`: Required (non-empty string)
- `message`: Required (non-empty string)

**Response (400 Bad Request):**
```json
{
    "message": "Failed to submit contact message.",
    "errors": {
        "email": ["Email is required."],
        "subject": ["Subject is required."]
    }
}
```

---

### Newsletter

#### Subscribe to Newsletter
**Endpoint:** `POST /api/newsletter/subscribe/`

**Request Body:**
```json
{
    "email": "subscriber@example.com"
}
```

**Response (201 Created):**
```json
{
    "message": "Successfully subscribed to newsletter.",
    "data": {
        "id": 1,
        "email": "subscriber@example.com",
        "subscribed_at": "2025-12-06T10:40:00Z"
    }
}
```

**Validation Rules:**
- `email`: Required, must be valid email format, and must be unique

**Response (400 Bad Request):**
```json
{
    "message": "Failed to subscribe to newsletter.",
    "errors": {
        "email": ["This email is already subscribed to our newsletter."]
    }
}
```

---

## Booking Types

The following booking types are supported:

- `chalet` - Chalet accommodation
- `campsite` - Campsite accommodation
- `conference` - Conference facilities
- `event` - Event hosting
- `safari` - Safari drive experience

---

## Error Responses

All error responses follow a consistent format:

**400 Bad Request:**
```json
{
    "message": "Descriptive error message",
    "errors": {
        "field_name": ["Error message for this field"]
    }
}
```

**404 Not Found:**
```json
{
    "message": "Resource not found."
}
```

**500 Internal Server Error:**
```json
{
    "message": "An unexpected error occurred."
}
```

---

## Testing with cURL

### Create a Booking
```bash
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "chalet",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+27712345678",
    "check_in": "2025-12-20",
    "check_out": "2025-12-25",
    "guests": 4,
    "message": "Looking forward!"
  }'
```

### Check Availability
```bash
curl http://localhost:8000/api/bookings/availability/?type=chalet&check_in=2025-12-20&check_out=2025-12-25
```

### Get Booking by Confirmation Number
```bash
curl http://localhost:8000/api/bookings/A7F3B2C8E5D1/
```

### Submit Contact Form
```bash
curl -X POST http://localhost:8000/api/contact/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane@example.com",
    "subject": "Inquiry",
    "message": "I have a question..."
  }'
```

### Subscribe to Newsletter
```bash
curl -X POST http://localhost:8000/api/newsletter/subscribe/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "subscriber@example.com"
  }'
```

---

## File Structure

```
bookings/
├── models.py          # Booking model definition
├── serializers.py     # BookingSerializer and AvailabilitySerializer
├── views.py           # BookingCreateView, AvailabilityCheckView, BookingDetailView
└── urls.py            # Bookings app URL configuration

contact/
├── models.py          # ContactMessage model definition
├── serializers.py     # ContactSerializer
├── views.py           # ContactCreateView
└── urls.py            # Contact app URL configuration

newsletter/
├── models.py          # Subscriber model definition
├── serializers.py     # SubscriberSerializer
├── views.py           # SubscriberCreateView
└── urls.py            # Newsletter app URL configuration

lodge_backend/
├── settings.py        # Django settings (includes REST_FRAMEWORK and app configs)
├── urls.py            # Main URL configuration
└── wsgi.py            # WSGI application

manage.py              # Django management script
```

---

## Key Features

✅ **Automatic Confirmation Numbers** - Each booking gets a unique confirmation number  
✅ **Availability Checking** - Check for overlapping bookings before confirming  
✅ **Email Validation** - All email fields are validated  
✅ **Date Validation** - Check-in/check-out dates are validated  
✅ **Duplicate Prevention** - Newsletter prevents duplicate email subscriptions  
✅ **Proper HTTP Status Codes** - RESTful responses with appropriate status codes  
✅ **Consistent Response Format** - All endpoints follow the same response structure  

---

## Next Steps

1. **Add Authentication** - Implement token-based authentication for admin endpoints
2. **Add Pagination** - Add pagination for list endpoints
3. **Add Filters** - Filter bookings by date range or type
4. **CORS Configuration** - Configure CORS for frontend integration
5. **Email Notifications** - Send confirmation emails for bookings and contact forms
6. **Admin Interface** - Customize Django admin for managing data
7. **Tests** - Add comprehensive unit and integration tests
8. **API Documentation** - Generate automated API docs with Swagger/OpenAPI

