from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, Float, Enum, JSON, Column
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class UserRole(str, enum.Enum):
	patient = "patient"
	doctor = "doctor"



class User(Base):
	__tablename__ = "users"

	id = Column(Integer, primary_key=True, index=True)
	email = Column(String, unique=True, index=True, nullable=False)
	full_name = Column(String, nullable=False)
	role = Column(Enum(UserRole), default=UserRole.patient, index=True)
	hashed_password = Column(String, nullable=False)
	created_at = Column(DateTime, default=datetime.utcnow)

	sessions = relationship("Session", back_populates="patient")



class Session(Base):
	__tablename__ = "sessions"

	id = Column(Integer, primary_key=True, index=True)
	patient_id = Column(Integer, ForeignKey("users.id"), index=True)
	exercise_name = Column(String, index=True)
	video_path = Column(String, nullable=False)
	started_at = Column(DateTime, default=datetime.utcnow)
	completed_at = Column(DateTime, nullable=True)
	# Added fields
	duration_seconds = Column(Integer, default=0)
	form_score = Column(Float, nullable=True)
	repetitions_count = Column(Integer, default=0)
	status = Column(String, default='completed')

	patient = relationship("User", back_populates="sessions")
	results = relationship("ExerciseResult", back_populates="session", cascade="all, delete-orphan")



class ExerciseResult(Base):
	__tablename__ = "exercise_results"

	id = Column(Integer, primary_key=True, index=True)
	session_id = Column(Integer, ForeignKey("sessions.id"), index=True)
	frame_index = Column(Integer)
	predicted_label = Column(String, index=True)
	confidence = Column(Float)
	pose_keypoints = Column(JSON)
	timestamp = Column(DateTime, default=datetime.utcnow)
	# Added field
	exercise_name = Column(String, index=True)

	session = relationship("Session", back_populates="results")

