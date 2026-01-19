# Payment & Booking Endpoints - Quick Reference

## Payment Verification Flow

```
Frontend Payment Redirect
         ↓
POST /api/payments/verify/
         ↓
Returns: {
  success: true,
  data: {
    booking: {
      name, type, check_in, check_out, guests,
      confirmation_number, email, phone, amount
    }
  }
}
         ↓
Display Confirmation Modal
```

## Key Endpoints

### 1. Verify Payment (POST)
```
POST /api/payments/verify/

Request:  { "reference": "paystack_ref" }
Response: {
  "success": true,
  "data": {
    "booking_id": 1,
    "order_id": "uuid",
    "reference": "paystack_ref",
    "status": "paid",
    "booking": {
      "confirmation_number": "B0535279-780",
      "name": "Guest Name",
      "type": "chalet",
      "check_in": "2026-05-14",
      "check_out": "2026-05-19",
      "guests": 2,
      "email": "guest@email.com",
      "phone": "+27123456789",
      "amount": 4000.00
    }
  }
}

Error: { "success": false, "error": "Payment not verified" }
```

### 2. Get Confirmation (GET)
```
GET /api/paystack/confirmation/{order_id}/

Response: {
  "success": true,
  "data": {
    "order_id": "uuid",
    "reference": "paystack_ref",
    "status": "paid",
    "amount": 4000.00,
    "booking": {
      "confirmation_number": "B0535279-780",
      "name": "Guest Name",
      "type": "chalet",
      "check_in": "2026-05-14",
      "check_out": "2026-05-19",
      "guests": 2,
      "email": "guest@email.com",
      "phone": "+27123456789"
    }
  }
}

Error: { "success": false, "error": "Order not found" }
```

### 3. Get Booking Details (GET)
```
GET /api/bookings/{confirmation_number}/

Response: {
  "success": true,
  "data": {
    "confirmation_number": "B0535279-780",
    "name": "Guest Name",
    "type": "chalet",
    "check_in": "2026-05-14",
    "check_out": "2026-05-19",
    "guests": 2,
    "email": "guest@email.com",
    "phone": "+27123456789",
    "status": "confirmed",
    "amount": 4000.00
  }
}

Error: { "success": false, "error": "Booking not found" }
```

## Frontend Integration

### Confirmation Modal Data
Use any of these endpoints depending on context:

| Use Case | Endpoint | When |
|----------|----------|------|
| After payment | `/api/payments/verify/` | User just paid |
| Confirmation page | `/api/paystack/confirmation/{order_id}/` | Revisiting confirmation |
| Booking details | `/api/bookings/{confirmation_number}/` | Any time with confirmation # |

### Modal Fields
```javascript
{
  confirmationNumber: booking.confirmation_number,
  guestName: booking.name,
  bookingType: booking.type,
  checkIn: booking.check_in,        // "2026-05-14"
  checkOut: booking.check_out,      // "2026-05-19"
  numberOfGuests: booking.guests,   // 2
  totalAmount: booking.amount,      // 4000.00
  email: booking.email,
  phone: booking.phone,
  status: booking.status            // "confirmed"
}
```

## Response Format Standard

All endpoints follow this pattern:

**Success (200/201):**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error (400/404/500):**
```json
{
  "success": false,
  "error": "Error message",
  "details": "Optional additional info"
}
```

## Date Format
All dates are in **ISO format**: `YYYY-MM-DD`
- check_in: "2026-05-14"
- check_out: "2026-05-19"

## Amount Format
All amounts are in **float with 2 decimals**: `NNNN.NN`
- Example: 4000.00
- Stored in database as: ZAR (rand)
- Sent to Paystack as: cents (multiply by 100)
- Returned to frontend as: ZAR (float)

## Error Codes

| Status | Error | When |
|--------|-------|------|
| 200 | ✓ Success | Normal response |
| 400 | Invalid request | Missing/invalid parameters |
| 404 | Not found | Booking/order doesn't exist |
| 500 | Server error | Unexpected error |
| 503 | Service error | Payment service unavailable |

## Implementation Status

✅ Payment verification endpoint returns booking details
✅ Confirmation endpoint returns booking details
✅ Booking detail endpoint returns all required fields
✅ All responses follow consistent format
✅ Proper error handling with appropriate status codes
✅ Dates in ISO format (YYYY-MM-DD)
✅ Amounts in ZAR for frontend display
