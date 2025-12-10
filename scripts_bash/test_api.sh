#!/bin/bash
# Test Booking API Endpoints - Complete Test Suite
# This script tests all booking endpoints and verifies confirmation_number is returned

BASE_URL="http://127.0.0.1:8000/api/bookings"
CONTENT_TYPE="Content-Type: application/json"

echo "================================================"
echo "Testing Ikhaya Lami Lodge Booking API"
echo "================================================"
echo ""

# 1. Create a Booking (POST) - Verify confirmation_number is returned
echo "1️⃣  CREATE BOOKING (POST /api/bookings/)"
echo "---"
BOOKING_RESPONSE=$(curl -s -X POST "$BASE_URL/" \
  -H "$CONTENT_TYPE" \
  -d '{
    "type": "chalet",
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "+27712345678",
    "check_in": "2025-12-15",
    "check_out": "2025-12-18",
    "guests": 3,
    "message": "Beach vacation with family!"
  }')

echo "$BOOKING_RESPONSE" | jq .
echo ""

# Extract confirmation_number from response
CONFIRMATION=$(echo "$BOOKING_RESPONSE" | jq -r '.data.confirmation_number // "N/A"')
echo "📝 Confirmation Number: $CONFIRMATION"
echo ""
echo "================================================"
echo ""

# 2. List All Bookings (GET)
echo "2️⃣  LIST ALL BOOKINGS (GET /api/bookings/)"
echo "---"
curl -s -X GET "$BASE_URL/" \
  -H "$CONTENT_TYPE" | jq .
echo ""
echo "================================================"
echo ""

# 3. Get Booking Details (GET by confirmation_number)
if [ "$CONFIRMATION" != "N/A" ]; then
  echo "3️⃣  GET BOOKING DETAILS (GET /api/bookings/$CONFIRMATION/)"
  echo "---"
  curl -s -X GET "$BASE_URL/$CONFIRMATION/" \
    -H "$CONTENT_TYPE" | jq .
  echo ""
  echo "================================================"
  echo ""

  # 4. Cancel Booking (PATCH)
  echo "4️⃣  CANCEL BOOKING (PATCH /api/bookings/$CONFIRMATION/cancel/)"
  echo "---"
  CANCEL_RESPONSE=$(curl -s -X PATCH "$BASE_URL/$CONFIRMATION/cancel/" \
    -H "$CONTENT_TYPE")
  echo "$CANCEL_RESPONSE" | jq .
  echo ""
  echo "================================================"
  echo ""

  # 5. Get Cancelled Booking (should still exist with status='cancelled')
  echo "5️⃣  GET CANCELLED BOOKING (status should be 'cancelled')"
  echo "---"
  curl -s -X GET "$BASE_URL/$CONFIRMATION/" \
    -H "$CONTENT_TYPE" | jq '.data | {confirmation_number, status, name, email}'
  echo ""
  echo "================================================"
  echo ""

  # 6. Delete Booking (DELETE)
  echo "6️⃣  DELETE BOOKING (DELETE /api/bookings/$CONFIRMATION/)"
  echo "---"
  curl -s -X DELETE "$BASE_URL/$CONFIRMATION/" \
    -H "$CONTENT_TYPE" | jq .
  echo ""
  echo "================================================"
  echo ""

  # 7. Try to Get Deleted Booking (should return 404)
  echo "7️⃣  GET DELETED BOOKING (should return 404 Not Found)"
  echo "---"
  curl -s -X GET "$BASE_URL/$CONFIRMATION/" \
    -H "$CONTENT_TYPE" | jq .
  echo ""
else
  echo "❌ Failed to extract confirmation_number from booking creation response"
fi

echo "================================================"
echo "8️⃣  CHECK AVAILABILITY (GET /api/bookings/availability/)"
echo "---"
curl -s -X GET "$BASE_URL/availability/?type=chalet&check_in=2025-12-20&check_out=2025-12-25" \
  -H "$CONTENT_TYPE" | jq .
echo ""
echo "================================================"
curl "$BASE_URL/bookings/availability/?type=chalet&check_in=2025-12-15&check_out=2025-12-18"
echo -e "\n"

# 4. Test contact form
echo "➡️ Submitting contact form..."
curl -X POST $BASE_URL/contact/ \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Charlie",
    "email":"charlie@example.com",
    "subject":"Booking enquiry",
    "message":"Do you have availability for 3 guests?"
  }'
echo -e "\n"

# 5. Test newsletter subscription
echo "➡️ Subscribing to newsletter..."
curl -X POST $BASE_URL/newsletter/subscribe/ \
  -H "Content-Type: application/json" \
  -d '{"email":"newguest@example.com"}'
echo -e "\n"

echo "✅ Reset and tests complete!"

 Run migrations at the end
echo "➡️ Applying migrations..."
cd ..   # move up from scripts_bash into lodge_backend root
python manage.py makemigrations
python manage.py migrate
cd scripts_bash   # go back into scripts_bash if you want
echo "✅ Migrations applied!"