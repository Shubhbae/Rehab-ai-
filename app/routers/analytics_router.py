import os
import numpy as np
from typing import List, Dict, Optional
from collections import Counter
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_role
from app.database import get_db
from app.models import UserRole, Session as DbSession, ExerciseResult
from app.schemas import ProgressSummary

router = APIRouter(prefix="/analytics", tags=["analytics"]) 


@router.get("/patient/{patient_id}", response_model=ProgressSummary)
async def patient_progress(patient_id: int, db: Session = Depends(get_db), user=Depends(require_role(UserRole.doctor))):
	sessions = db.query(DbSession).filter(DbSession.patient_id == patient_id).all()
	session_ids = [s.id for s in sessions]
	results = db.query(ExerciseResult).filter(ExerciseResult.session_id.in_(session_ids)).all() if session_ids else []
	label_counts = Counter(r.predicted_label for r in results)
	last_active = max((r.timestamp for r in results), default=None)
	return ProgressSummary(
		patient_id=patient_id,
		total_sessions=len(sessions),
		total_frames=len(results),
		label_distribution=dict(label_counts),
		last_active=last_active,
	)

