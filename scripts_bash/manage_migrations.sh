#!/bin/bash
# Helper script to run Django migrations in order

echo "=== Step 1: Making migrations ==="
python manage.py makemigrations

echo "=== Step 2: Applying migrations ==="
python manage.py migrate

echo "=== Step 3: Collecting static files (optional, for admin panel) ==="
python manage.py collectstatic --noinput

echo "=== Step 4: Running quick test suite (optional) ==="
python manage.py test

echo "=== All migration steps completed successfully ==="
