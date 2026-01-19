# start_backend.ps1
Write-Host "Activating virtual environment..."
.\venv\Scripts\Activate.ps1

Write-Host "Starting Django server..."
python manage.py runserver 0.0.0.0:8000
