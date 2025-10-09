from fastapi import APIRouter

# Define the router at module scope so imports never fail due to optional deps
router = APIRouter()


@router.get("/database/health")
def database_health():
    """Test database connection against the configured SQLite file."""
    try:
        # Import locally to avoid hard dependency at module import time
        from sqlalchemy import create_engine, text  # type: ignore

        engine = create_engine("sqlite:///./rehab.db")
        with engine.connect() as connection:
            _ = connection.execute(text("SELECT 1"))
        return {
            "success": True,
            "message": "Database connection successful",
            "database_url": "sqlite:///./rehab.db",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/database/ping")
def database_ping():
    return {"status": "ok"}
