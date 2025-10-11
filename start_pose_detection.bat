@echo off
echo ========================================
echo POSE DETECTION SYSTEM STARTUP
echo ========================================
echo.

echo Step 1: Installing Flask dependencies...
pip install flask flask-cors flask-socketio

echo.
echo Step 2: Testing the system...
python test_flask_backend.py

echo.
echo Step 3: Starting Flask backend...
echo The backend will run on http://localhost:8000
echo Open test_frontend.html in your browser to test
echo.
echo Press Ctrl+C to stop the backend
echo.

python flask_backend.py

pause


