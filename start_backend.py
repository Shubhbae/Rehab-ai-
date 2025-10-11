#!/usr/bin/env python3
"""
Start the backend server for real-time tracking
"""
import subprocess
import sys
import os

def start_backend():
    print("🚀 Starting Rehab AI Backend Server...")
    print("📍 Server will run on: http://localhost:8000")
    print("🔗 WebSocket endpoint: ws://localhost:8000/realtime/ws")
    print("\n📋 What's working:")
    print("   ✅ MoveNet pose detection")
    print("   ✅ LSTM exercise classification (mock mode)")
    print("   ✅ Real-time skeleton tracking")
    print("   ✅ WebSocket communication")
    print("\n🎯 Next steps:")
    print("   1. Keep this terminal open")
    print("   2. Open another terminal")
    print("   3. Run: cd 'frontend cursor' && npm run dev")
    print("   4. Go to patient dashboard")
    print("   5. Click 'Start Camera' then 'Start AI Analysis'")
    print("\n" + "="*50)
    
    try:
        # Start the FastAPI server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 Backend server stopped!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    start_backend()






