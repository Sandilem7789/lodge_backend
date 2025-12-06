#!/bin/bash
echo "🚀 Starting Ikhaya Lami Lodge backend..."

# Navigate to project root
cd ..

# Pull latest changes from GitHub
git pull origin main

# Apply migrations
python manage.py migrate

# Start the server
python manage.py runserver
