# Payment Verification Endpoint (/api/payments/verify/)

## Endpoint Details

**Method:** POST  
**URL:** `/api/payments/verify/`  
**Content-Type:** application/json

## Request Format

```json
{
  "reference": "paystack_transaction_reference"
}
```

**Required Fields:**
- `reference` - Paystack transaction reference from payment completion

## Success Response (200 OK)

```json
{
  "success": true,
  "data": {
    "reference": "paystack_transaction_reference",
    "confirmation_number": "B0535279-780",
    "booking": {
      "name": "Sandile Mathenjwa",
      "type": "chalet",
      "check_in": "2026-05-14",
      "check_out": "2026-05-19",
      "guests": 2
    }
  }
}
```

**Response Fields:**
- `success` (boolean) - Indicates successful verification
- `reference` (string) - Paystack transaction reference
- `confirmation_number` (string) - Booking confirmation number for guest reference
- `booking` (object) - Booking details:
  - `name` - Guest name
  - `type` - Booking type (chalet, campsite, conference, safari, event)
  - `check_in` - Check-in date (YYYY-MM-DD format)
  - `check_out` - Check-out date (YYYY-MM-DD format)
  - `guests` - Number of guests (integer)

## Failure Responses

### Payment Verification Failed (400 Bad Request)

```json
{
  "success": false,
  "error": "Payment not verified",
  "reference": "paystack_transaction_reference"
}
```

### Order Not Found (404 Not Found)

```json
{
  "success": false,
  "error": "Order not found"
}
```

### Missing Reference (400 Bad Request)

```json
{
  "success": false,
  "error": "reference is required"
}
```

### Service Error (503 Service Unavailable)

```json
{
  "success": false,
  "error": "Payment service error"
}
```

### Server Error (500 Internal Server Error)

```json
{
  "success": false,
  "error": "Internal server error"
}
```

## Frontend Usage Example

```typescript
async function verifyPayment(reference: string) {
  const response = await fetch('/api/payments/verify/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ reference }),
  });

  const result = await response.json();

  if (!result.success) {
    console.error('Payment verification failed:', result.error);
    return;
  }

  // Use the data for confirmation modal
  const { reference, confirmation_number, booking } = result.data;
  
  displayConfirmationModal({
    confirmationNumber: confirmation_number,
    guestName: booking.name,
    bookingType: booking.type,
    checkIn: booking.check_in,
    checkOut: booking.check_out,
    numberOfGuests: booking.guests,
  });
}
```

## Data Flow

1. **User completes payment** on Paystack
2. **Frontend receives reference** from Paystack callback/redirect
3. **Frontend calls POST /api/payments/verify/** with reference
4. **Backend verifies** with Paystack API
5. **Backend updates** order and booking status to "paid"/"confirmed"
6. **Backend returns** confirmation number and booking details
7. **Frontend displays** confirmation modal with booking information

## Implementation Checklist

✅ Endpoint accepts reference parameter
✅ Verifies with Paystack API
✅ Updates order status to "paid"
✅ Updates booking status to "confirmed"
✅ Returns success flag
✅ Returns reference for receipt
✅ Returns confirmation_number for booking reference
✅ Returns all required booking fields (name, type, check_in, check_out, guests)
✅ Dates in ISO format (YYYY-MM-DD)
✅ Handles verification failures with clear error messages
✅ Handles missing order with 404 response
✅ Handles missing reference with 400 response
✅ Handles Paystack API errors gracefully

## Error Handling

| Error | HTTP Status | Message | Cause |
|-------|------------|---------|-------|
| reference required | 400 | "reference is required" | Request missing reference parameter |
| Order not found | 404 | "Order not found" | Reference doesn't match any order |
| Payment not verified | 400 | "Payment not verified" | Paystack verification failed |
| Service error | 503 | "Payment service error" | Paystack API unavailable |
| Server error | 500 | "Internal server error" | Unexpected server error |

## BookingSerializer Fields Confirmation

All required fields are included in BookingSerializer:
- ✅ `name` - Guest name
- ✅ `type` - Booking type
- ✅ `check_in` - Check-in date
- ✅ `check_out` - Check-out date
- ✅ `guests` - Number of guests
- ✅ `confirmation_number` - Booking reference
- Plus additional fields: email, phone, status, amount, created_at, etc.

## Validation Rules

- `reference` must match a stored Paystack reference in Order model
- `check_in` must be a valid date before `check_out`
- `guests` must be positive integer
- `name` must not be empty
- `type` must be valid booking type
- Response dates always in ISO format (YYYY-MM-DD)
