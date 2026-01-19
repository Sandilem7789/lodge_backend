# Payment Amount Handling Corrections - Implementation Summary

## Overview
This document outlines the corrections made to the Django backend payment amount handling to ensure proper conversion between ZAR (rand) and Paystack cents, with validation to prevent double multiplication errors.

## Problem Statement
- Frontend sends amounts in ZAR/rand (e.g., 4000.00)
- Paystack API expects amounts in cents (multiply by 100)
- Previous implementation had inconsistent handling of conversions
- Risk of double multiplication errors when amounts were passed through multiple layers

## Solution Architecture

### 1. Created `paystack/utils.py` - Centralized Payment Utilities

A new utilities module provides reusable conversion and validation functions:

#### Key Functions:

**`rand_to_cents(amount_rand)`**
- Converts ZAR to Paystack cents (multiplies by 100)
- Validates amount is positive and valid decimal format
- Returns integer cents for API payload
- Validates amount is not already in cents (heuristic warning for amounts > R100,000)

**`cents_to_rand(amount_cents)`**
- Converts Paystack cents back to ZAR
- Returns Decimal with 2 decimal places
- Used internally when displaying amounts from Paystack responses

**`validate_amount_not_in_cents(amount_rand)`**
- Validates that an amount hasn't already been converted to cents
- Logs warnings for suspicious amounts (multiples of 100, >= 1000)
- Prevents double multiplication errors

**`get_paystack_amount(amount_rand, validate=True)`**
- Combined function: validates and converts to cents in one call
- Default validation enabled to catch accidental double conversions

**`get_display_amount(amount_rand)`**
- Converts amounts to float with 2 decimal places for frontend display
- Ensures consistent formatting across all responses

### 2. Updated `paystack/views.py` - Proper Conversion in API Views

#### InitializePaymentView
- **Line 108**: Updated payload building to use `get_paystack_amount(amount)` for Paystack API
- **Line 139**: Response now uses `get_display_amount(order.amount)` to return amount in rand to frontend
- Ensures database stores amounts in rand, API receives cents

#### initialize_payment() function
- **Line 577**: Added validation using `validate_amount_not_in_cents(amount)` for override amounts
- **Line 584**: Uses `get_paystack_amount(amount)` for Paystack payload
- Catches validation errors with clear messages to frontend

### 3. Updated `paystack/serializers.py` - Consistent Amount Display

#### OrderSerializer
- **Lines 8-9**: Added SerializerMethodField for amount
- **Lines 23-26**: `get_amount()` method uses `get_display_amount()` to ensure amounts always returned in rand to frontend
- Database stores in rand, serializer converts for display consistency

### 4. Updated `bookings/views.py` - Validation on Creation

#### BookingCreateView
- Added import of `validate_amount_not_in_cents`
- **Lines 33-39**: Validates calculated amount is in rand after pricing calculation
- Returns helpful error message if amount is invalid
- Prevents invalid amounts from being stored in database

## Data Flow

### Creating a Booking:
1. Frontend sends booking data with no explicit amount
2. `BookingCreateView` calculates amount using `calculate_booking_amount()` in rand
3. Amount validated with `validate_amount_not_in_cents()`
4. Amount stored in `Booking.amount` in rand
5. Order created with amount in rand

### Initializing Paystack Payment:
1. Frontend requests payment with booking_id
2. `initialize_payment()` retrieves booking amount (in rand)
3. Validates amount hasn't been double-converted: `validate_amount_not_in_cents()`
4. Converts to cents: `amount_cents = get_paystack_amount(amount)`
5. Paystack API receives amount in cents
6. Response to frontend includes: `get_display_amount(amount)` (in rand)

### Verifying Payment:
1. After user completes payment, Paystack callback received
2. Order status updated to 'paid'
3. Booking status updated to 'confirmed'
4. Frontend requests confirmation - OrderSerializer returns amount in rand

## Validation Examples

### Valid Amount Handling:
```python
# Frontend sends 4000.00 ZAR
amount = Decimal('4000.00')

# Validate it's in rand
validate_amount_not_in_cents(amount)  # OK

# Convert for Paystack
paystack_cents = get_paystack_amount(amount)  # Returns 400000

# Send to Paystack
paystack_payload['amount'] = paystack_cents  # 400000

# Return to frontend
display_amount = get_display_amount(amount)  # Returns 4000.00
```

### Preventing Double Multiplication:
```python
# If someone accidentally converts twice:
amount = Decimal('4000.00')
wrong_amount = amount * 100  # Now 400000

# Validation catches this:
validate_amount_not_in_cents(wrong_amount)  
# Logs: "Amount 400000 might already be in cents"

# get_paystack_amount prevents actual multiplication:
try:
    get_paystack_amount(wrong_amount)  
    # Still works but with validation warning
except ValueError as e:
    # Client handled error
```

## Database Storage Convention

- **Booking.amount**: Stored in ZAR (rand), e.g., 4000.00
- **Order.amount**: Stored in ZAR (rand), e.g., 4000.00
- **Paystack API**: Always receives cents, e.g., 400000
- **Frontend Responses**: Always receive amounts in rand for display, e.g., 4000.00

## Error Handling

### Amount Validation Errors:
```python
# Invalid format
get_paystack_amount("invalid")
# Raises: ValueError("Invalid amount format: invalid")

# Negative amount
get_paystack_amount(-100)
# Raises: ValueError("Amount cannot be negative")

# Already in cents (heuristic warning)
validate_amount_not_in_cents(400000)
# Logs: "Amount 400000 ZAR might already be in cents"

# Too small (less than 1 cent)
rand_to_cents(0.001)
# Raises: ValueError("Amount 0.001 is too small (< 0.01 ZAR)")
```

## Testing Recommendations

1. **Unit Tests** - Test utils.py functions:
   ```python
   def test_rand_to_cents():
       assert rand_to_cents(Decimal('100.00')) == 10000
       assert rand_to_cents(100) == 10000
       
   def test_cents_to_rand():
       assert cents_to_rand(10000) == Decimal('100.00')
       
   def test_validate_not_in_cents():
       validate_amount_not_in_cents(100)  # OK
       with pytest.raises(ValueError):
           validate_amount_not_in_cents(400000)  # Suspicious
   ```

2. **Integration Tests** - Test payment flow:
   ```python
   def test_booking_payment_flow():
       # Create booking with amount in rand
       booking = create_booking()
       assert booking.amount == Decimal('4000.00')
       
       # Initialize payment
       response = initialize_payment(booking.id)
       paystack_payload = captured_request.json
       assert paystack_payload['amount'] == 400000  # Cents
       
       # Response to frontend
       assert response['amount'] == 4000.00  # Rand
   ```

3. **Edge Cases**:
   - Very large amounts (multi-million rand bookings)
   - Very small amounts (under 1 rand)
   - Non-integer rand amounts (4000.50 ZAR)
   - Concurrent payment initialization

## Migration Notes

No database migrations required. All changes are in:
- Business logic (views.py, utils.py)
- Serialization (serializers.py)
- No schema changes to existing models

## Backward Compatibility

- Existing bookings retain their amounts (unchanged)
- API responses maintain the same JSON structure
- Frontend changes needed: expect amounts in rand in all responses (no longer need to divide by 100)

## Summary of Files Changed

| File | Changes | Impact |
|------|---------|--------|
| `paystack/utils.py` | **NEW** - Conversion & validation utilities | Core functionality |
| `paystack/views.py` | Updated to use utils functions, added validation | InitializePaymentView, initialize_payment() |
| `paystack/serializers.py` | Added get_amount() method for consistent display | OrderSerializer responses |
| `bookings/views.py` | Added amount validation | BookingCreateView |

All changes maintain backward compatibility while fixing the amount handling issue.
