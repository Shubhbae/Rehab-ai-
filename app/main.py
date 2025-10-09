from fastapi import FastAPI
import cv2
import base64
import numpy as np
from pydantic_settings import BaseSettings
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from sqlalchemy import text

# Import your routers
from .routers import auth_router, patients_router  # Add other routers as needed
from .routers import classification_router, realtime_router
from .routers import database_router

app = FastAPI(title="Rehab AI Backend", version="1.0.0")

# Add CORS middleware for frontend communication
app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		"http://localhost:3000",    # React default
		"http://localhost:3001",    # Alternative React port
		"http://localhost:5173",    # Vite default
		"http://localhost:8080",    # Your React app port
		"http://127.0.0.1:3000",    # Alternative localhost
		"http://127.0.0.1:5173",    # Alternative localhost
		"http://127.0.0.1:8080"     # Your React app localhost
	],
	allow_credentials=True,
	allow_methods=["*"],            # Allow all HTTP methods
	allow_headers=["*"],            # Allow all headers
)

# Include your routers with proper API prefixes
app.include_router(auth_router.router, prefix="/api/auth", tags=["authentication"])
app.include_router(patients_router.router, prefix="/api/patients", tags=["patients"])
app.include_router(classification_router.router)
app.include_router(realtime_router.router)
app.include_router(database_router.router, prefix="/api", tags=["database"])

# Add other routers as needed (uncomment when you have them):
# from .routers import doctor_router, profile_router
# app.include_router(doctor_router.router, prefix="/api/doctor", tags=["doctor"])
# app.include_router(profile_router.router, prefix="/api/profile", tags=["profile"])

# Health check endpoint
@app.get("/")
def read_root():
	return {"message": "Rehab AI Backend is running!"}

@app.get("/api/health")
def health_check():
	return {"status": "healthy", "message": "Backend is operational"}


@app.on_event("startup")
def startup_create_tables():
    print("[Startup] Initializing database and creating tables...")
    try:
        # Ensure models are imported so SQLAlchemy is aware of all tables
        from . import models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        print("[Startup] ✅ Database tables ensured.")
    except Exception as e:
        print(f"[Startup] ❌ Failed to create tables: {e}")

@app.on_event("startup")
async def startup_load_models():
	print("[Startup] Initializing models...")
	try:
		from .services.lstm_service import LSTMClassifier
		print("[Startup] Creating LSTMClassifier instance...")
		app.state.lstm = LSTMClassifier()
		print("[Startup] ✅ LSTMClassifier initialized.")
	except Exception as e:
		print(f"[Startup] ❌ Failed to initialize LSTMClassifier: {e}")


@app.post("/api/test/user")
def create_test_user():
	"""Create a test user to verify database connectivity."""
	try:
		# Use the existing SQLAlchemy engine; use named params with text()
		with engine.begin() as conn:
			conn.execute(text(
				"""
				CREATE TABLE IF NOT EXISTS users (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					email TEXT UNIQUE,
					name TEXT,
					role TEXT
				)
				"""
			))
			conn.execute(
				text("INSERT OR IGNORE INTO users (email, name, role) VALUES (:email, :name, :role)"),
				{"email": "test@example.com", "name": "Test User", "role": "patient"},
			)
		return {"success": True, "message": "Test user created successfully"}
	except Exception as e:
		return {"success": False, "error": str(e)}

@app.get("/api/camera/test")
def test_camera():
	"""Test camera access"""
	try:
		cap = cv2.VideoCapture(0)
		if not cap.isOpened():
			return {"success": False, "error": "Camera not accessible"}
		ret, frame = cap.read()
		if not ret:
			cap.release()
			return {"success": False, "error": "Failed to capture frame"}
		_, buffer = cv2.imencode('.jpg', frame)
		frame_base64 = base64.b64encode(buffer).decode('utf-8')
		cap.release()
		return {
			"success": True,
			"message": "Camera accessed successfully",
			"frame_shape": list(frame.shape),
			"frame_preview": f"data:image/jpeg;base64,{frame_base64[:100]}..."
		}
	except Exception as e:
		return {"success": False, "error": str(e)}

