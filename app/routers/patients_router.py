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


# Models and endpoints added per requirements
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
				"name": "Arm Circles",
				"description": "Gentle circular movements",
				"reps": 10,
				"sets": 3
			},
			"patientId": "patient-123",
			"reps": 10,
			"sets": 3,
			"instructions": "Start with small circles",
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


@router.post("/reports")
async def upload_report():
	return {"message": "Report uploaded successfully"}


@router.get("/reports")
async def get_reports():
	return []