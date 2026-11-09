"""
Cloud OS Backend - Main FastAPI Application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import redis
from config import settings
from models import Base
from routes.auth import router as auth_router
from routes.workspaces import router as workspaces_router
from routes.sessions import router as sessions_router
from websocket.routes import router as websocket_router

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Database setup
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=10,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis setup
redis_client = redis.from_url(settings.REDIS_URL)

# Create database tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    # Startup
    logger.info(f"Starting Cloud OS Backend - Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL}")
    logger.info(f"Redis: {settings.REDIS_URL}")
    
    # Test database connection
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("✓ Database connection successful")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        raise
    
    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("✓ Redis connection successful")
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Cloud OS Backend")
    redis_client.close()


# Create FastAPI app
app = FastAPI(
    title="Cloud OS API",
    description="Production-grade open-source cloud operating system for AI development",
    version="0.1.0",
    lifespan=lifespan
)

# ==============================================================================
# Middleware Setup
# ==============================================================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.local"]
)


# ==============================================================================
# Exception Handlers
# ==============================================================================

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# ==============================================================================
# Health Check Endpoints
# ==============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0"
    }


@app.get("/health/ready")
async def readiness_check():
    """Readiness check - verifies dependencies"""
    checks = {}
    
    # Database check
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
    
    # Redis check
    try:
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
    
    all_ok = all(v == "ok" for v in checks.values())
    
    return {
        "status": "ready" if all_ok else "not_ready",
        "checks": checks
    }


# ==============================================================================
# API Routes (placeholder - will be added)
# ==============================================================================

# Include auth routes
app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(sessions_router)
app.include_router(websocket_router)

@app.get("/api/v1")
async def api_root():
    """API root endpoint"""
    return {
        "name": "Cloud OS API",
        "version": "v1",
        "endpoints": {
            "auth": "/api/v1/auth",
            "workspaces": "/api/v1/workspaces",
            "sessions": "/api/v1/sessions",
            "workflows": "/api/v1/workflows",
            "providers": "/api/v1/providers",
            "storage": "/api/v1/storage"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
