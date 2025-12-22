# Paystack Quick Reference

## Setup (5 mins)

```bash
# 1. Update .env
PAYSTACK_SECRET_KEY=sk_test_xxxxxxxxxxxxx
PAYSTACK_PUBLIC_KEY=pk_test_xxxxxxxxxxxxx
PAYSTACK_CURRENCY=ZAR

# 2. Install dependencies (if not already)
pip install python-decouple requests

# 3. Verify setup
python manage.py check
```

## API Endpoints

```bash
# Initialize payment
POST /api/paystack/initialize-payment/
{
  "booking_id": 123,
  "email": "customer@example.com",
  "callback_url": "https://yourdomain.com/payment-callback/"
}

# Callback (called by Paystack)
GET /api/paystack/callback/?reference=paystack_ref_xxx

# Get confirmation
GET /api/paystack/confirmation/{order_id}/

# List orders
GET /api/paystack/orders/
GET /api/paystack/orders/?status=paid
GET /api/paystack/orders/?booking_id=123
```

## Payment Flow

```
1. POST /initialize-payment/ → Get authorization_url
2. Redirect user to authorization_url (Paystack checkout)
3. User fills payment details
4. Paystack calls callback with reference
5. Backend verifies transaction
6. User sees confirmation page
```

## Test Cards

| Type | Card | Expiry | CVV |
|------|------|--------|-----|
| Success | 4084084084084081 | 12/25 | 123 |
| Failure | 5555555555554444 | 12/25 | 123 |

(Test mode only; use mode 1 for live)

## Logging

```bash
# Watch payment logs
tail -f logs/paystack.log

# View all logs
tail -f logs/django.log
```

## File Locations

| File | Purpose |
|------|---------|
| `.env` | API keys |
| `paystack/models.py` | Order model |
| `paystack/views.py` | Payment endpoints |
| `paystack/urls.py` | Routes |
| `settings.py` | Paystack config |
| `PAYSTACK_INTEGRATION.md` | Full docs |

## Common Issues

| Issue | Solution |
|-------|----------|
| `Missing required fields` | Check payload has booking_id, email, callback_url |
| `Invalid API key` | Verify PAYSTACK_SECRET_KEY in .env |
| `Connection refused` | Ensure internet; Paystack API is accessible |
| `Order not found` | Check reference parameter in callback |

## Frontend Template

```typescript
const initializePayment = async (bookingId, email) => {
  const res = await fetch('/api/paystack/initialize-payment/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      booking_id: bookingId,
      email,
      callback_url: window.location.origin + '/payment-callback'
    })
  });
  const data = await res.json();
  window.location.href = data.data.authorization_url; // Redirect to Paystack
};
```

## Pricing

```python
# in paystack/views.py
pricing = {
    'chalet': 800,      # ZAR/night
    'campsite': 200,    # ZAR/night
    'conference': 5000, # ZAR flat
    'safari': 2500,     # ZAR flat
    'event': 1000,      # ZAR flat
}
```

## Production Checklist

- [ ] Update .env keys to live mode (`sk_live_*`, `pk_live_*`)
- [ ] Enable HTTPS (DEBUG=False, SECURE_SSL_REDIRECT=True)
- [ ] Set ALLOWED_HOSTS to your domain
- [ ] Test with live test cards
- [ ] Monitor `logs/paystack.log`
- [ ] Configure Paystack webhook (optional)
- [ ] Set callback URL in Paystack dashboard

## Need Help?

1. Check `PAYSTACK_INTEGRATION.md` for full guide
2. Review `logs/paystack.log` for errors
3. Verify API keys on https://dashboard.paystack.com/settings/developer
4. See Paystack docs: https://paystack.com/docs/payments/
