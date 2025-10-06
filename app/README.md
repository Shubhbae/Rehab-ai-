# Rehab Exercise Classification Backend (FastAPI)

FastAPI backend that accepts videos, extracts poses with MoveNet, classifies sequences with a trained LSTM model (squat, step_jack, half_wheel), stores results in SQLite, provides REST APIs, and a realtime WebSocket for webcam.

## Setup

1. Create and activate venv (Windows PowerShell):
```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
```

2. Install dependencies:
```powershell
pip install -r requirements.txt
```

3. Provide your trained LSTM model at `models/lstm_model.h5`.

4. Run the server:
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Auth
- Signup: `POST /auth/signup` with `{ email, full_name, password, role }`
- Login: `POST /auth/login` form fields: `username`, `password`. Returns JWT.
- Use `Authorization: Bearer <token>` for protected endpoints.

## Endpoints
- Patients (doctor role): `GET /patients`, `GET /patients/{id}`, `GET /patients/{id}/sessions`
- Classification: `POST /classify/video` (multipart form with `file`, `exercise_name`).
- Analytics (doctor role): `GET /analytics/patient/{patient_id}`
- Realtime WebSocket: `ws://<host>/realtime/ws` sending `{ "image_b64": "..." }` per frame.

## Notes
- SQLite file: `rehab.db`
- Uploaded videos stored in `media/`
- MoveNet from TF Hub: thunder singlepose
- CORS is open for development; tighten for production.

