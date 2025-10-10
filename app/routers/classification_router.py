import os
from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Session as DbSession, ExerciseResult
from app.schemas import SessionRead, ClassificationSummary
from app.services.movenet_service import MoveNetService
from app.services.lstm_service import LSTMClassifier, LABELS

router = APIRouter(prefix="/classify", tags=["classification"]) 

movenet = MoveNetService()
lstm = LSTMClassifier()


@router.get("/labels")
async def get_labels():
	return {"labels": LABELS}


@router.post("/video", response_model=ClassificationSummary)
async def classify_video(
	file: UploadFile = File(...),
	exercise_name: str = Form(...),
	db: Session = Depends(get_db),
	user = Depends(get_current_user),
):
	if user.role not in ("patient", "doctor"):
		raise HTTPException(status_code=403, detail="Unauthorized role")

	# Save upload
	filename = f"{user.id}_{exercise_name}_{file.filename}"
	video_path = os.path.join(settings.media_dir, filename)
	with open(video_path, "wb") as f:
		f.write(await file.read())

	# Create session
	session = DbSession(patient_id=user.id, exercise_name=exercise_name, video_path=video_path)
	db.add(session)
	db.commit()
	db.refresh(session)

	# Process video -> poses
	poses = movenet.process_video(video_path)

	# Classify per frame
	preds = lstm.predict_per_frame(poses)

	# Store results
	for p in preds:
		res = ExerciseResult(
			session_id=session.id,
			frame_index=p["frame_index"],
			predicted_label=p["label"],
			confidence=p["confidence"],
			pose_keypoints=poses[p["frame_index"]],
			exercise_name=exercise_name,
		)
		db.add(res)
	db.commit()

	# Summary
	counts = {label: 0 for label in LABELS}
	for p in preds:
		counts[p["label"]] += 1

	return ClassificationSummary(
		session_id=session.id,
		exercise_name=exercise_name,
		predicted_counts=counts,
	)


@router.post("/video/detect")
async def classify_video_detect(
	file: UploadFile = File(...),
	user = Depends(get_current_user),
):
	try:
		if user.role not in ("patient", "doctor"):
			raise HTTPException(status_code=403, detail="Unauthorized role")

		# Save upload temporarily
		filename = f"{user.id}_detect_{file.filename}"
		video_path = os.path.join(settings.media_dir, filename)
		with open(video_path, "wb") as f:
			f.write(await file.read())

		# Process video and predict overall exercise
		poses = movenet.process_video(video_path)
		label, confidence, _ = lstm.predict_sequence(poses)

		# Keep API label exactly as produced by model; message is human-friendly
		message = f"Detected exercise: {label.replace('_', ' ').title()}"
		return {
			"success": True,
			"exercise": label,
			"confidence": confidence,
			"message": message,
		}
	except Exception as e:
		return {"success": False, "error": str(e)}

