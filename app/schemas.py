from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from app.models import UserRole


class Token(BaseModel):
	access_token: str
	token_type: str = "bearer"


class TokenData(BaseModel):
	email: Optional[str] = None
	role: Optional[UserRole] = None


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.patient


class UserCreate(UserBase):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    password: str = Field(min_length=6)


class UserRead(UserBase):
	id: int
	full_name: str
	created_at: datetime

	class Config:
		from_attributes = True


class SessionCreate(BaseModel):
	exercise_name: str


class SessionRead(BaseModel):
	id: int
	patient_id: int
	exercise_name: str
	video_path: str
	started_at: datetime
	completed_at: Optional[datetime]

	class Config:
		from_attributes = True


class ExerciseResultRead(BaseModel):
	id: int
	session_id: int
	frame_index: int
	predicted_label: str
	confidence: float
	pose_keypoints: dict
	timestamp: datetime

	class Config:
		from_attributes = True


class ClassificationSummary(BaseModel):
	session_id: int
	exercise_name: str
	predicted_counts: dict[str, int]
	accuracy: Optional[float] = None


class ProgressSummary(BaseModel):
	patient_id: int
	total_sessions: int
	total_frames: int
	label_distribution: dict[str, int]
	last_active: Optional[datetime]

