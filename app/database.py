from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings
import os

# Ensure media and models directories exist at startup
os.makedirs(settings.media_dir, exist_ok=True)
os.makedirs(settings.models_dir, exist_ok=True)

engine = create_engine(
	settings.database_url,
	connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
	pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()


def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

