# Payment Amount Handling - Quick Reference

## The Rule
- **Database & Frontend**: Use ZAR (rand) - e.g., 4000.00
- **Paystack API**: Use cents - e.g., 400000
- **Conversion**: 1 ZAR = 100 cents

## When to Use Each Function

### Converting ZAR to Cents (for Paystack API)
```python
from paystack.utils import get_paystack_amount

# Best way - includes validation
amount_cents = get_paystack_amount(amount_zar)

# Or explicit conversion
amount_cents = rand_to_cents(amount_zar)  # 4000.00 → 400000
```

### Converting Cents to ZAR (from Paystack API)
```python
from paystack.utils import cents_to_rand

amount_zar = cents_to_rand(amount_cents)  # 400000 → 4000.00
```

### Validating Amount is in Correct Format
```python
from paystack.utils import validate_amount_not_in_cents

# Checks if amount hasn't already been converted
validate_amount_not_in_cents(amount)  # Raises ValueError if suspicious
```

### Formatting for Frontend Display
```python
from paystack.utils import get_display_amount

# Always use this when sending amounts to frontend
response_amount = get_display_amount(order.amount)  # → 4000.0
```

## Common Patterns

### Pattern 1: Creating a Payment
```python
# Amount comes in from user (in ZAR)
amount = request.data.get('amount')  # 4000.00

# Validate it's in rand, not cents
validate_amount_not_in_cents(amount)

# Store in database (in rand)
booking.amount = Decimal(str(amount))
booking.save()

# Send to Paystack (in cents)
paystack_payload['amount'] = get_paystack_amount(amount)
```

### Pattern 2: Returning Payment Info to Frontend
```python
from paystack.serializers import OrderSerializer

# Database has amount in rand
order = Order.objects.get(id=order_id)
# order.amount = Decimal('4000.00')

# Serializer automatically converts for display
serializer = OrderSerializer(order)
# serializer.data['amount'] = 4000.0 (float in rand)
```

### Pattern 3: Payment Verification from Paystack
```python
# Paystack returns amount in cents
paystack_response = verify_with_paystack(reference)
paystack_cents = paystack_response['data']['amount']  # 400000

# Convert back to rand for comparison
paystack_zar = cents_to_rand(paystack_cents)  # 4000.00

# Compare with order (stored in rand)
if order.amount == paystack_zar:
    # Amount matches!
    pass
```

## What NOT to Do

❌ **Don't manually multiply by 100**
```python
# WRONG
paystack_payload['amount'] = int(order.amount * 100)

# RIGHT
paystack_payload['amount'] = get_paystack_amount(order.amount)
```

❌ **Don't assume Paystack amounts are already in cents**
```python
# WRONG - this causes double multiplication
paystack_payload['amount'] = int(order.amount * 100)  # 4000 * 100 = 400000
paystack_payload['amount'] = paystack_payload['amount'] * 100  # DON'T!

# RIGHT
paystack_payload['amount'] = get_paystack_amount(order.amount)
```

❌ **Don't send cents to frontend**
```python
# WRONG - frontend expects rand
return Response({'amount': 400000})  # Confusing!

# RIGHT
return Response({'amount': get_display_amount(order.amount)})
```

❌ **Don't mix storage formats**
```python
# WRONG - inconsistent storage
booking.amount = Decimal('4000.00')  # Rand
order.amount = 400000  # Cents - INCONSISTENT!

# RIGHT - always store in rand
booking.amount = Decimal('4000.00')
order.amount = Decimal('4000.00')
```

## Debugging Checklist

If amounts look wrong, check:

1. **Database**: Is amount stored in rand? (typically 100-10000)
   ```python
   order = Order.objects.get(id=1)
   print(order.amount)  # Should be Decimal('4000.00'), not 400000
   ```

2. **Paystack Payload**: Is amount in cents? (typically 10000-1000000)
   ```python
   print(paystack_payload['amount'])  # Should be 400000, not 4000
   ```

3. **API Response**: Is amount in rand? (typically 100-10000)
   ```python
   # When you GET an order, amount should be 4000.0 not 400000
   ```

4. **Validation**: Run validation check
   ```python
   from paystack.utils import validate_amount_not_in_cents
   validate_amount_not_in_cents(order.amount)
   # If it logs a warning, amount might be wrong
   ```

## Error Messages

| Message | Cause | Fix |
|---------|-------|-----|
| "Invalid amount format" | Amount couldn't be converted to Decimal | Pass valid number or Decimal |
| "Amount cannot be negative" | Negative amount passed | Validate input is positive |
| "Amount is too small (< 0.01 ZAR)" | Amount less than 1 cent | Use amounts >= 0.01 ZAR |
| "might already be in cents" | Heuristic warning | Review where amount came from |

## Key Files Reference

- **`paystack/utils.py`**: All conversion & validation functions
- **`paystack/views.py`**: Uses functions for InitializePaymentView & initialize_payment()
- **`paystack/serializers.py`**: OrderSerializer uses get_display_amount()
- **`bookings/views.py`**: BookingCreateView validates amounts

---

**Remember**: ZAR in database/frontend, cents for Paystack API only!
