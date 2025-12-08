#!/bin/bash
echo "🔄 Resetting and testing Ikhaya Lami Lodge API endpoints..."

BASE_URL="http://127.0.0.1:8000/api"

# 0. List all current bookings
echo "➡️ Listing current bookings..."
curl -s $BASE_URL/bookings/ | jq
echo -e "\n"

# 1. Delete all bookings (loop through confirmation numbers)
echo "➡️ Deleting all bookings..."
for CONF in $(curl -s $BASE_URL/bookings/ | jq -r '.[]?.confirmation_number'); do
  echo "Deleting booking $CONF..."
  curl -X DELETE $BASE_URL/bookings/$CONF/
done
echo -e "\n"

# 2. Add fresh bookings
echo "➡️ Creating new bookings..."
curl -X POST $BASE_URL/bookings/ \
  -H "Content-Type: application/json" \
  -d '{
    "type":"chalet",
    "name":"Alice",
    "email":"alice@example.com",
    "phone":"111111111",
    "check_in":"2025-12-15",
    "check_out":"2025-12-18",
    "guests":2,
    "message":"First test booking"
  }'
echo -e "\n"

curl -X POST $BASE_URL/bookings/ \
  -H "Content-Type: application/json" \
  -d '{
    "type":"campsite",
    "name":"Bob",
    "email":"bob@example.com",
    "phone":"222222222",
    "check_in":"2025-12-20",
    "check_out":"2025-12-22",
    "guests":4,
    "message":"Second test booking"
  }'
echo -e "\n"

# 3. Test availability
echo "➡️ Checking availability..."
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