# Ikhaya Lami Lodge Backend

A Django REST Framework backend for managing bookings, availability checks, contact messages, and newsletter subscriptions for **Ikhaya Lami Lodge**.  
This API powers the lodge’s frontend booking system and provides an admin dashboard for staff.

---

## 🚀 Features
- **Bookings API**
  - Create new bookings
  - List all bookings
  - Retrieve booking by confirmation number
  - Cancel bookings (status update)
  - Delete bookings (hard removal)
- **Availability API**
  - Check availability for chalets, campsites, conferences, events, and safari drives
- **Contact API**
  - Lodge contact form submissions
- **Newsletter API**
  - Subscribe users to lodge updates
- **Paystack Payments** (Mobile-First Server-Initialized Flow)
  - Initialize transactions with Paystack API
  - Full-page redirect (works on all mobile browsers)
  - Server-side payment verification
  - Manual verify endpoint for testing/webhooks
- **Admin Dashboard**
  - Manage bookings, users, and cancellations via Django Admin

---

## 🛠️ Tech Stack
- **Backend**: Django, Django REST Framework
- **Database**: SQLite (default, can be swapped for PostgreSQL/MySQL)
- **Auth**: Django built-in (JWT optional for future)
- **Testing**: Bash scripts with `curl`
- **Payments**: Paystack (mobile-optimized server-initialized flow)

---

## 💳 Paystack Payment Integration

This backend implements a **mobile-first payment flow** using Paystack's server-initialized transactions.

**Key Features:**
- ✅ **Full-page redirects** (works on all mobile browsers)
- ✅ **Server-side verification** (secure, webhook-ready)
- ✅ **No popup/iframe limitations** (fixes mobile browser blocking)

**Endpoints:**
- `POST /api/payments/initialize/` - Initialize transaction, get Paystack authorization URL
- `GET /api/paystack/callback/` - Paystack callback (auto-verify after payment)
- `POST /api/payments/verify/` - Manual transaction verification

**For complete integration guide, see:** [PAYSTACK_MOBILE_INTEGRATION.md](PAYSTACK_MOBILE_INTEGRATION.md)

### Quick Start
1. Set environment variables:
   ```bash
   PAYSTACK_SECRET_KEY=sk_live_xxx...
   PAYSTACK_PUBLIC_KEY=pk_live_xxx...
   PAYSTACK_CURRENCY=ZAR
   ```
2. Frontend calls `POST /api/payments/initialize/` with booking data
3. Backend returns `authorization_url` from Paystack
4. Frontend redirects to Paystack payment page
5. After payment, Paystack redirects to `/api/paystack/callback/?reference=...`
6. Backend verifies and updates booking status

### Testing
```bash
# Run payment tests
python manage.py test paystack.tests

# Run specific test class
python manage.py test paystack.tests.PaymentMobileFlowTests
```

---

## ⚙️ Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/lodge_backend.git
   cd lodge_backend
