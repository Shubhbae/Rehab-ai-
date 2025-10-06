from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.auth_router import router as auth_router
from .routers.patients_router import router as patients_router
from .routers.classification_router import router as classification_router
from .routers.analytics_router import router as analytics_router
from .routers.realtime_router import router as realtime_router

app = FastAPI(title=settings.app_name)

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Create tables on startup for simplicity; for production, use Alembic migrations
Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(classification_router)
app.include_router(analytics_router)
app.include_router(realtime_router)


@app.get("/")
async def root():
	return {"status": "ok", "app": settings.app_name}

