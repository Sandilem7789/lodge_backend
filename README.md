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
- **Admin Dashboard**
  - Manage bookings, users, and cancellations via Django Admin

---

## 🛠️ Tech Stack
- **Backend**: Django, Django REST Framework
- **Database**: SQLite (default, can be swapped for PostgreSQL/MySQL)
- **Auth**: Django built-in (JWT optional for future)
- **Testing**: Bash scripts with `curl`

---

## ⚙️ Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/lodge_backend.git
   cd lodge_backend
