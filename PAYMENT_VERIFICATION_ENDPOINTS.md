# Payment Verification Endpoints - Implementation Summary

## Overview
Updated payment verification endpoints to return comprehensive booking details for the frontend confirmation modal. All endpoints now use consistent response format with booking information.

## Endpoints Updated

### 1. Verify Payment Endpoint
**POST /api/payments/verify/**

Verifies Paystack payment and returns booking details for confirmation modal.

#### Request
```json
{
  "reference": "paystack_transaction_reference"
}
```

#### Success Response (200 OK)
```json
{
  "success": true,
  "data": {
    "booking_id": 1,
    "order_id": "550e8400-e29b-41d4-a716-446655440000",
    "reference": "paystack_transaction_reference",
    "status": "paid",
    "booking": {
      "confirmation_number": "B0535279-780",
      "name": "Sandile Mathenjwa",
      "type": "chalet",
      "check_in": "2026-05-14",
      "check_out": "2026-05-19",
      "guests": 2,
      "email": "sandile@example.com",
      "phone": "+27123456789",
      "amount": 4000.00
    }
  }
}
```

#### Failure Response - Payment Not Verified (400 Bad Request)
```json
{
  "success": false,
  "error": "Payment not verified",
  "reference": "paystack_transaction_reference"
}
```

#### Failure Response - Order Not Found (404 Not Found)
```json
{
  "success": false,
  "error": "Order not found"
}
```

#### Failure Response - API Error (400 Bad Request)
```json
{
  "success": false,
  "error": "Payment not verified",
  "details": "Paystack error message"
}
```

#### Failure Response - Service Error (503 Service Unavailable)
```json
{
  "success": false,
  "error": "Payment service error"
}
```

#### Failure Response - Server Error (500 Internal Server Error)
```json
{
  "success": false,
  "error": "Internal server error"
}
```

---

### 2. Payment Confirmation Endpoint
**GET /api/paystack/confirmation/<order_id>/**

Returns payment and booking details for a confirmed order.

#### Success Response (200 OK)
```json
{
  "success": true,
  "data": {
    "order_id": "550e8400-e29b-41d4-a716-446655440000",
    "reference": "paystack_transaction_reference",
    "status": "paid",
    "amount": 4000.00,
    "booking": {
      "confirmation_number": "B0535279-780",
      "name": "Sandile Mathenjwa",
      "type": "chalet",
      "check_in": "2026-05-14",
      "check_out": "2026-05-19",
      "guests": 2,
      "email": "sandile@example.com",
      "phone": "+27123456789"
    }
  }
}
```

#### Failure Response - Order Not Found (404 Not Found)
```json
{
  "success": false,
  "error": "Order not found",
  "order_id": "invalid_order_id"
}
```

#### Failure Response - Server Error (500 Internal Server Error)
```json
{
  "success": false,
  "error": "An error occurred"
}
```

---

## Implementation Details

### File: `paystack/views.py`

#### verify_payment() Function Changes

**Location:** Lines 412-475

**Key Changes:**
1. ✅ After successful payment verification, builds comprehensive booking object
2. ✅ Returns all required booking fields: name, type, check_in, check_out, guests, confirmation_number
3. ✅ Includes contact info (email, phone) for customer confirmation
4. ✅ Includes order details (order_id, reference, status)
5. ✅ Converts dates to ISO format (YYYY-MM-DD)
6. ✅ Converts amount to float for display
7. ✅ Standardized error responses with "Payment not verified" message
8. ✅ Handles null values safely (e.g., amount might be None)

**Response Structure:**
```python
{
    'success': True,
    'data': {
        'booking_id': int,
        'order_id': str,
        'reference': str,
        'status': 'paid',
        'booking': {
            'confirmation_number': str,
            'name': str,
            'type': str,
            'check_in': 'YYYY-MM-DD',
            'check_out': 'YYYY-MM-DD',
            'guests': int,
            'email': str,
            'phone': str,
            'amount': float,
        }
    }
}
```

#### PaymentConfirmationView Changes

**Location:** Lines 262-310

**Key Changes:**
1. ✅ Updated response format to use `success` flag
2. ✅ Returns comprehensive booking and order details
3. ✅ Includes customer contact information
4. ✅ Converts dates to ISO format
5. ✅ Proper error handling with `success: false`
6. ✅ Consistent response structure with verify_payment endpoint

---

## Frontend Integration

### Payment Verification Flow

```typescript
// After Paystack payment completion
async function verifyPayment(reference: string) {
  try {
    const response = await fetch('/api/payments/verify/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ reference }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const result = await response.json();

    if (!result.success) {
      showError(result.error);
      return;
    }

    // Show confirmation modal with booking details
    const booking = result.data.booking;
    showConfirmationModal({
      guestName: booking.name,
      confirmationNumber: booking.confirmation_number,
      bookingType: booking.type,
      checkIn: booking.check_in,
      checkOut: booking.check_out,
      numberOfGuests: booking.guests,
      totalAmount: booking.amount,
      email: booking.email,
      phone: booking.phone,
    });

  } catch (error) {
    showError('Payment verification failed. Please try again.');
  }
}
```

### Confirmation Modal Retrieval

```typescript
// Get payment confirmation by order ID
async function getPaymentConfirmation(orderId: string) {
  try {
    const response = await fetch(
      `/api/paystack/confirmation/${orderId}/`
    );

    const result = await response.json();

    if (!result.success) {
      showError(result.error);
      return;
    }

    // Display confirmation details
    displayOrderConfirmation(result.data);

  } catch (error) {
    showError('Failed to retrieve confirmation details');
  }
}
```

---

## Required Fields in Response

### For Confirmation Modal Display
| Field | Source | Format | Purpose |
|-------|--------|--------|---------|
| name | booking.name | String | Guest name display |
| type | booking.type | String | Room/service type |
| check_in | booking.check_in | YYYY-MM-DD | Check-in date |
| check_out | booking.check_out | YYYY-MM-DD | Check-out date |
| guests | booking.guests | Integer | Number of guests |
| confirmation_number | booking.confirmation_number | String | Booking reference |
| amount | booking.amount | Float | Total cost |
| email | booking.email | String | Contact email |
| phone | booking.phone | String | Contact phone |

### For Order Tracking
| Field | Source | Format | Purpose |
|-------|--------|--------|---------|
| order_id | order.order_id | UUID String | Order reference |
| reference | order.reference | String | Paystack reference |
| status | order.status | String | Payment status |
| booking_id | booking.id | Integer | Database reference |

---

## Error Handling

### Payment Verification Errors

| Scenario | Status | Error Message | Action |
|----------|--------|---------------|--------|
| Reference missing | 400 | "reference is required" | Validate request |
| Order not found | 404 | "Order not found" | Check reference validity |
| Payment not verified | 400 | "Payment not verified" | Inform user to retry |
| Paystack API error | 400 | "Payment not verified" | Retry verification |
| Service unavailable | 503 | "Payment service error" | Suggest retry later |
| Server error | 500 | "Internal server error" | Log and investigate |

### Recovery Strategies

1. **Missing Reference:**
   - Ensure Paystack callback includes reference parameter
   - Frontend should capture reference from Paystack callback

2. **Order Not Found:**
   - Verify reference matches stored order in database
   - Check if order was created before payment attempt

3. **Payment Verification Failed:**
   - Display retry button for user
   - Log Paystack response for debugging
   - Contact support link for persistent issues

4. **Service Error:**
   - Show retry message to user
   - Implement exponential backoff for retries
   - Provide support contact information

---

## Data Validation

### Input Validation
- `reference`: String, required, matches stored Paystack reference
- `order_id`: String, required, valid UUID format

### Output Validation
- All booking dates are in YYYY-MM-DD format
- Amount is converted to float with proper decimal places
- Null values handled gracefully (check_in/check_out might be None for some booking types)
- Phone numbers returned as provided (no formatting applied)

---

## Testing Checklist

- [ ] Verify payment with valid reference returns booking details
- [ ] Verify payment with invalid reference returns 404
- [ ] Payment confirmation retrieves order details correctly
- [ ] All date fields formatted as YYYY-MM-DD
- [ ] Amount field is float type
- [ ] Response includes all required fields for modal display
- [ ] Error responses have consistent format
- [ ] Cancelled bookings still return confirmation details
- [ ] Amount conversion works correctly (ZAR display format)

---

## API Contract Summary

| Aspect | Value |
|--------|-------|
| Verify Payment Endpoint | POST /api/payments/verify/ |
| Confirmation Endpoint | GET /api/paystack/confirmation/<order_id>/ |
| Success Status | 200 OK |
| Success Format | { success: true, data: {...} } |
| Failure Status | 400/404/500 |
| Failure Format | { success: false, error: "..." } |
| Content-Type | application/json |
| Authentication | None required |

---

## Migration Notes

No database migrations required. Changes are to:
- Response formatting only
- View logic for data assembly
- No schema changes to existing models

All existing data is compatible with new response format.
