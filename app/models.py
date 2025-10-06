from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, Float, Enum, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
import enum


class UserRole(str, enum.Enum):
	patient = "patient"
	doctor = "doctor"


class User(Base):
	__tablename__ = "users"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
	full_name: Mapped[str] = mapped_column(String, nullable=False)
	role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.patient, index=True)
	hashed_password: Mapped[str] = mapped_column(String, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

	sessions: Mapped[list["Session"]] = relationship("Session", back_populates="patient")


class Session(Base):
	__tablename__ = "sessions"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
	exercise_name: Mapped[str] = mapped_column(String, index=True)
	video_path: Mapped[str] = mapped_column(String, nullable=False)
	started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
	completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
	# Added fields
	duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
	form_score: Mapped[float] = mapped_column(Float, nullable=True)
	repetitions_count: Mapped[int] = mapped_column(Integer, default=0)
	status: Mapped[str] = mapped_column(String, default='completed')

	patient: Mapped[User] = relationship("User", back_populates="sessions")
	results: Mapped[list["ExerciseResult"]] = relationship("ExerciseResult", back_populates="session", cascade="all, delete-orphan")


class ExerciseResult(Base):
	__tablename__ = "exercise_results"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)
	frame_index: Mapped[int] = mapped_column(Integer)
	predicted_label: Mapped[str] = mapped_column(String, index=True)
	confidence: Mapped[float] = mapped_column(Float)
	pose_keypoints: Mapped[dict] = mapped_column(JSON)
	timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
	# Added field
	exercise_name: Mapped[str] = mapped_column(String, index=True)

	session: Mapped[Session] = relationship("Session", back_populates="results")

