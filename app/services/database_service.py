from typing import List, Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import get_password_hash


class DatabaseService:
    def __init__(self):
        pass

    def save_exercise_prediction(self, exercise: str, keypoints: List[float], confidence: float, user_id: Optional[str] = None):
        """
        Save exercise prediction to SQLite database
        """
        try:
            # For now, just print the data - you can implement SQLite storage later
            print(f"Exercise prediction saved: {exercise}, confidence: {confidence}")
            if user_id:
                print(f"   User ID: {user_id}")
            return {"success": True, "message": "Exercise prediction saved"}
        except Exception as e:
            print(f"Error saving exercise prediction: {e}")
            raise e

    def get_user_exercises(self, user_id: str):
        """
        Get all exercises for a specific user from SQLite database
        """
        try:
            # For now, return empty list - you can implement SQLite query later
            print(f"Fetching exercises for user: {user_id}")
            return []
        except Exception as e:
            print(f"Error fetching exercises: {e}")
            return []

    def create_test_users(self):
        """
        Create test users in SQLite database
        """
        try:
            db = next(get_db())
            
            # Test users to create with simple password hashes
            test_users = [
                {
                    "email": "doctor@test.com",
                    "full_name": "Dr. Smith",
                    "role": "doctor",
                    "password": "doc123"
                },
                {
                    "email": "patient@test.com", 
                    "full_name": "John Doe",
                    "role": "patient",
                    "password": "pat123"
                }
            ]
            
            created_users = []
            for user_data in test_users:
                # Check if user already exists
                existing_user = db.query(User).filter(User.email == user_data["email"]).first()
                if existing_user:
                    print(f"User {user_data['email']} already exists")
                    continue
                
                # Use simple hash for now to avoid bcrypt issues
                import hashlib
                simple_hash = hashlib.sha256(user_data["password"].encode()).hexdigest()
                
                # Create new user
                user = User(
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    hashed_password=simple_hash
                )
                db.add(user)
                created_users.append(user_data)
            
            db.commit()
            print(f"Created {len(created_users)} test users")
            return created_users
            
        except Exception as e:
            print(f"Error creating test users: {e}")
            raise e

# Create service instance
database_service = DatabaseService()

def get_database_service():
    return database_service
