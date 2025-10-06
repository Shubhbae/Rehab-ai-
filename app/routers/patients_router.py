import os
import numpy as np
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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

