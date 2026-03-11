"""
FastAPI main application entry point for Flashcard Learning System.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

# Import database initialization
from app.database import init_db, get_db

# Import all route modules
from app.auth import routes as auth_routes
from app.datasets import routes as dataset_routes
from app.sessions import routes as session_routes
from app.gamification import routes as gamification_routes
from app.spaced import routes as spaced_routes
from app.dashboard import routes as dashboard_routes
from app.admin import routes as admin_routes

# Load environment variables
load_dotenv()

# Create FastAPI instance
app = FastAPI(
    title="Flashcard Learning System API",
    description="A spaced repetition flashcard learning system with gamification",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3002", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3002"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(dataset_routes.router, prefix="/api/v1")
app.include_router(session_routes.router, prefix="/api/v1")
app.include_router(gamification_routes.router, prefix="/api/v1")
app.include_router(spaced_routes.router, prefix="/api/v1")
app.include_router(dashboard_routes.router, prefix="/api/v1")
app.include_router(admin_routes.router, prefix="/api/v1")

# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint for health checking."""
    return {
        "message": "Flashcard Learning System API",
        "status": "healthy",
        "version": "1.0.0",
        "docs": "/docs",
        "modules": [
            "auth", "datasets", "sessions", 
            "gamification", "spaced", "dashboard", "admin"
        ]
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    try:
        # Test database connection
        db = next(get_db())
        db_status = "connected"
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "version": "1.0.0"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else "An error occurred"
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Actions to perform on application startup."""
    print("🚀 Flashcard Learning System API starting up...")
    print(f"📊 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔗 Database URL: {os.getenv('DATABASE_URL', 'Not configured')}")
    print(f"🌐 CORS Origins: {os.getenv('CORS_ORIGINS', 'http://localhost:3000')}")
    
    # Initialize database tables
    try:
        init_db()
        print("✅ Database tables initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Actions to perform on application shutdown."""
    print("🛑 Flashcard Learning System API shutting down...")

if __name__ == "__main__":
    # Development server configuration
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT", "development") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
