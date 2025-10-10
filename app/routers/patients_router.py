import os
import numpy as np
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.auth import require_role
from app.database import get_db
from app.models import User, UserRole, Session as DbSession
from app.schemas import UserRead, SessionRead

router = APIRouter(prefix="/patients", tags=["patients"]) 


# Models and endpoints added per requirements
_ASSIGNMENTS: Dict[str, List[Dict]] = {}

class AssignedExercise(BaseModel):
	id: str
	exerciseId: str
	exercise: dict
	patientId: str
	reps: int
	sets: int
	instructions: str
	status: str


@router.get("/exercises", response_model=List[AssignedExercise])
async def get_assigned_exercises():
	return [
		{
			"id": "assigned-1",
			"exerciseId": "ex-1",
			"exercise": {
				"id": "ex-1",
				"name": "Mountain Pose",
				"description": "Stand tall with feet together, arms at sides",
				"reps": 5,
				"sets": 3
			},
			"patientId": "patient-123",
			"reps": 5,
			"sets": 3,
			"instructions": "Hold for 30 seconds, focus on breathing",
			"status": "pending"
		},
		{
			"id": "assigned-2",
			"exerciseId": "ex-2",
			"exercise": {
				"id": "ex-2",
				"name": "Warrior 1",
				"description": "Lunge position with arms raised overhead",
				"reps": 3,
				"sets": 2
			},
			"patientId": "patient-123",
			"reps": 3,
			"sets": 2,
			"instructions": "Hold each side for 20 seconds",
			"status": "pending"
		},
		{
			"id": "assigned-3",
			"exerciseId": "ex-3",
			"exercise": {
				"id": "ex-3",
				"name": "Warrior 2",
				"description": "Side lunge with arms extended horizontally",
				"reps": 3,
				"sets": 2
			},
			"patientId": "patient-123",
			"reps": 3,
			"sets": 2,
			"instructions": "Hold each side for 20 seconds",
			"status": "pending"
		},
		{
			"id": "assigned-4",
			"exerciseId": "ex-4",
			"exercise": {
				"id": "ex-4",
				"name": "Tree Pose",
				"description": "Balance on one leg with foot on inner thigh",
				"reps": 2,
				"sets": 2
			},
			"patientId": "patient-123",
			"reps": 2,
			"sets": 2,
			"instructions": "Hold each side for 15 seconds",
			"status": "pending"
		},
		{
			"id": "assigned-5",
			"exerciseId": "ex-5",
			"exercise": {
				"id": "ex-5",
				"name": "Downward Dog",
				"description": "Inverted V-shape pose",
				"reps": 3,
				"sets": 2
			},
			"patientId": "patient-123",
			"reps": 3,
			"sets": 2,
			"instructions": "Hold for 10 seconds each time",
			"status": "pending"
		}
	]


@router.get("/progress")
async def get_progress():
	return []


@router.get("/ai-score")
async def get_ai_score():
	return {"score": 75, "message": "Great progress!"}


@router.post("/progress")
async def update_progress():
	return {"message": "Progress updated successfully"}


@router.get("/{patient_id}/reports")
async def get_reports(patient_id: str):
    # Placeholder for per-patient reports list
    return []


@router.post("/{patient_id}/reports")
async def upload_report(patient_id: str):
    return {"message": "Report uploaded successfully"}


# Place dynamic doctor-only routes AFTER static/patient routes to avoid conflicts
class PatientSummary(BaseModel):
    id: str
    full_name: str
    email: str
    msd_case: str


class ExerciseHistoryItem(BaseModel):
    date: str
    exercise_name: str
    repetitions: int
    sets: int
    form_score: float


class CreateAssignmentRequest(BaseModel):
    exercise_name: str
    repetitions: int
    sets: int
    due_date: str
    notes: Optional[str] = None


class AssignmentItem(BaseModel):
    id: str
    exercise_name: str
    repetitions: int
    sets: int
    due_date: str
    notes: Optional[str] = None
    status: str = "assigned"


@router.get("/roster", response_model=List[PatientSummary])
async def get_doctor_roster(user=Depends(require_role(UserRole.doctor))):
    return [
        {"id": "p-1", "full_name": "TUSHAR SHAHRIYA", "email": "tushar@example.com", "msd_case": "Lumbar strain (LBP)"},
        {"id": "p-2", "full_name": "SHUBH GAUTAM", "email": "shubh@example.com", "msd_case": "Cervical spondylosis"},
        {"id": "p-3", "full_name": "KAJAL KUKREJA", "email": "kajal@example.com", "msd_case": "Patellofemoral pain"},
        {"id": "p-4", "full_name": "ABHAY TIWARI", "email": "abhay@example.com", "msd_case": "Rotator cuff tendinopathy"},
        {"id": "p-5", "full_name": "RIJUL BANSAL", "email": "rijul@example.com", "msd_case": "Ankle sprain rehab"},
    ]


@router.get("/{patient_id}/history", response_model=List[ExerciseHistoryItem])
async def get_patient_history(patient_id: str, user=Depends(require_role(UserRole.doctor))):
    # mock history
    return [
        {"date": "2025-10-08", "exercise_name": "mountain_pose", "repetitions": 5, "sets": 2, "form_score": 0.82},
        {"date": "2025-10-09", "exercise_name": "warrior_1", "repetitions": 3, "sets": 2, "form_score": 0.76},
        {"date": "2025-10-10", "exercise_name": "tree_pose", "repetitions": 2, "sets": 2, "form_score": 0.88},
    ]


@router.get("/{patient_id}/assignments", response_model=List[AssignmentItem])
async def list_assignments(patient_id: str, user=Depends(require_role(UserRole.doctor))):
    return _ASSIGNMENTS.get(patient_id, [])


@router.post("/{patient_id}/assign", response_model=AssignmentItem)
async def create_assignment(patient_id: str, req: CreateAssignmentRequest, user=Depends(require_role(UserRole.doctor))):
    from uuid import uuid4
    item: AssignmentItem = AssignmentItem(
        id=str(uuid4()),
        exercise_name=req.exercise_name,
        repetitions=req.repetitions,
        sets=req.sets,
        due_date=req.due_date,
        notes=req.notes,
        status="assigned",
    )
    _ASSIGNMENTS.setdefault(patient_id, []).append(item.model_dump())
    return item

@router.get("/", response_model=List[UserRead])
async def list_patients(db: Session = Depends(get_db), user=Depends(require_role(UserRole.doctor))):
	return db.query(User).filter(User.role == UserRole.patient).all()


@router.get("/{patient_id}", response_model=UserRead)
async def get_patient(patient_id: int, db: Session = Depends(get_db), user=Depends(require_role(UserRole.doctor))):
	pat = db.query(User).filter(User.id == patient_id, User.role == UserRole.patient).first()
	if not pat:
		raise HTTPException(status_code=404, detail="Patient not found")
	return pat


@router.get("/{patient_id}/sessions", response_model=List[SessionRead])
async def list_patient_sessions(patient_id: int, db: Session = Depends(get_db), user=Depends(require_role(UserRole.doctor))):
	sessions = db.query(DbSession).filter(DbSession.patient_id == patient_id).order_by(DbSession.started_at.desc()).all()
	return sessions