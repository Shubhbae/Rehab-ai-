from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import authenticate_user, create_access_token, get_password_hash
from app.config import settings
from app.database import get_db
from app.models import User, UserRole
from app.schemas import UserCreate, UserRead, Token

router = APIRouter(prefix="/auth", tags=["auth"]) 


@router.post("/signup", response_model=UserRead)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
	exists = db.query(User).filter(User.email == user_in.email).first()
	if exists:
		raise HTTPException(status_code=400, detail="Email already registered")
	user = User(
		email=user_in.email,
		full_name=user_in.full_name,
		role=user_in.role,
		hashed_password=get_password_hash(user_in.password),
	)
	db.add(user)
	db.commit()
	db.refresh(user)
	return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
	user = authenticate_user(db, form_data.username, form_data.password)
	if not user:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
	access_token = create_access_token(
		data={"sub": user.email, "role": user.role.value},
		expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
	)
	return {"access_token": access_token, "token_type": "bearer"}


# Login models compatible with simplified login flow
class LoginRequest(BaseModel):
	email: str
	password: str
	role: str  # "patient" or "doctor"


class LoginResponse(BaseModel):
	user: dict
	token: str


@router.post("/send-otp")
async def send_otp(phone: str, role: str):
	return {"message": "OTP sent successfully"}


@router.post("/verify-otp")
async def verify_otp(phone: str, otp: str, role: str):
	return {"user": {"id": "user-123"}, "token": "fake-jwt-token"}


@router.post("/logout")
async def logout():
	return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user():
	return {"id": "user-123", "email": "test@example.com", "role": "patient"}

