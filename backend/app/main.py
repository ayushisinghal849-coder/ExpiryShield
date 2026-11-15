from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
import app.models  # Ensure all SQLAlchemy models are registered
from app.seed.demo_data import seed_database

# Import routers
from app.api.inventory import router as inventory_router
from app.api.stores import router as stores_router
from app.api.analysis import router as analysis_router
from app.api.recommendations import router as recommendations_router
from app.api.approvals import router as approvals_router
from app.api.analytics import router as analytics_router
from app.api.scenarios import router as scenarios_router

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="ExpiryShield Backend API - Intelligent inventory expiry and cross-store rebalancing",
    version="0.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(inventory_router)
app.include_router(stores_router)
app.include_router(analysis_router)
app.include_router(recommendations_router)
app.include_router(approvals_router)
app.include_router(analytics_router)
app.include_router(scenarios_router)

@app.on_event("startup")
def startup_event():
    # Automatically seed demo data if tables are empty
    from app.core.database import SessionLocal
    from app.models.store import Store
    db = SessionLocal()
    try:
        if db.query(Store).count() == 0:
            seed_database(db)
    finally:
        db.close()

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": "0.1.0"
    }

@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "health": "/health",
        "docs": "/docs"
    }
