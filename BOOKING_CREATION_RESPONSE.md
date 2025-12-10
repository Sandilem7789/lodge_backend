# Booking Creation Response Format

This document demonstrates the complete response format when creating a booking via `POST /api/bookings/`.

## Request

```bash
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "chalet",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "123456789",
    "check_in": "2025-12-10",
    "check_out": "2025-12-12",
    "guests": 2,
    "message": "Looking forward to my stay!"
  }'
```

## Response (201 Created)

```json
{
  "message": "Booking created successfully.",
  "data": {
    "id": 1,
    "type": "chalet",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "123456789",
    "check_in": "2025-12-10",
    "check_out": "2025-12-12",
    "guests": 2,
    "message": "Looking forward to my stay!",
    "status": "confirmed",
    "confirmation_number": "ABC123DEF456",
    "created_at": "2025-12-08T09:19:32.614246Z"
  }
}
```

## Key Fields Included

✅ **confirmation_number** - Unique identifier for the booking (UUID-based, auto-generated)  
✅ **status** - Current booking status (default: "confirmed")  
✅ **type** - Booking type (chalet, campsite, conference, event, safari)  
✅ **name** - Guest name  
✅ **email** - Guest email  
✅ **phone** - Guest phone number  
✅ **check_in** - Check-in date (YYYY-MM-DD)  
✅ **check_out** - Check-out date (YYYY-MM-DD)  
✅ **guests** - Number of guests  
✅ **message** - Optional booking message  
✅ **created_at** - Booking creation timestamp (ISO 8601)  
✅ **id** - Database ID

## Frontend Usage

The frontend can immediately use the `confirmation_number` from the response for:
- Displaying the booking confirmation
- Sharing with the guest
- Future API calls to retrieve/cancel/delete the booking

## Example: Retrieving a Booking

Once you have the `confirmation_number`, retrieve the booking details:

```bash
curl -X GET http://localhost:8000/api/bookings/ABC123DEF456/ \
  -H "Content-Type: application/json"
```

## Example: Cancelling a Booking

Mark a booking as cancelled (without deleting it):

```bash
curl -X PATCH http://localhost:8000/api/bookings/ABC123DEF456/cancel/ \
  -H "Content-Type: application/json"
```

Response will show `"status": "cancelled"` and the booking remains in the database for reporting.

## Example: Deleting a Booking

Permanently remove a booking from the database:

```bash
curl -X DELETE http://localhost:8000/api/bookings/ABC123DEF456/ \
  -H "Content-Type: application/json"
```

---

## Implementation Details

### BookingSerializer
- Located in: `bookings/serializers.py`
- Includes all fields from the Booking model
- `confirmation_number` is auto-generated as a UUID (first 12 characters in uppercase)
- `status` defaults to "confirmed" on creation
- All validations are applied (email format, date validation, etc.)

### BookingListCreateView
- Located in: `bookings/views.py`
- Handles `POST /api/bookings/` for creation
- Handles `GET /api/bookings/` to list all bookings
- Returns full serialized booking data in response

### Testing
A test script is available: `test_booking_creation.py`

```bash
python test_booking_creation.py
```

This verifies that all required fields are present in the response.
