"""
Temporary simple FastAPI app for testing timer functionality with SQLite
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import SQLite auth
from sqlite_auth import router as auth_router

# Create FastAPI instance
app = FastAPI(
    title="Flashcard Learning System API",
    description="A spaced repetition flashcard learning system with gamification",
    version="1.0.0"
)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3002",  # Alternative port
    "http://127.0.0.1:3002",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router)

# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint for health checking."""
    return {"message": "Flashcard Learning System API", "status": "running"}

@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "version": "1.0.0"
    }

# Simple datasets endpoint for testing
@app.get("/api/v1/datasets/")
async def list_datasets():
    """Temporary datasets endpoint"""
    return [
        {
            "id": "test-dataset-1",
            "name": "Test Dataset",
            "description": "A test dataset for timer functionality",
            "element_count": 10,
            "created_at": "2025-08-04T16:00:00Z"
        }
    ]

# Simple session endpoints for timer testing
@app.post("/api/v1/sessions/start")
async def start_session(session_data: dict):
    """Start a learning session with timer support"""
    return {
        "learning_set_id": "test-session-1",
        "dataset_id": session_data.get("dataset_id", "test-dataset-1"),
        "stage": 1,
        "status": "active",
        "mode": "progressive",
        "total_items": 10,
        "timer_enabled": session_data.get("timer_enabled", False),
        "timer_seconds": session_data.get("timer_seconds", 30),
        "timer_mode": session_data.get("timer_mode", "optional")
    }

@app.get("/api/v1/sessions/next")
async def get_next_flashcard(learning_set_id: str):
    """Get next flashcard for testing"""
    return {
        "element_id": "test-element-1",
        "question_field": "question",
        "question_value": "What is 2 + 2?",
        "question_type": "text",
        "answer_field": "answer",
        "choices": ["3", "4", "5", "6"],
        "correct_answer": "4",
        "timer_enabled": True,
        "timer_seconds": 30,
        "timer_mode": "optional"
    }

@app.post("/api/v1/sessions/answer")
async def submit_answer(answer_data: dict):
    """Submit an answer"""
    return {
        "correct": answer_data.get("is_correct", True),
        "success_streak": 1,
        "next_due": "2025-08-05T16:00:00Z",
        "status": "correct",
        "explanation": "Good job!",
        "timer_performance": "excellent" if answer_data.get("response_time_ms", 0) < 15000 else "good",
        "time_bonus": 10 if answer_data.get("response_time_ms", 0) < 15000 else 0
    }

@app.get("/api/v1/sessions/progress")
async def get_session_progress(learning_set_id: str):
    """Get session progress"""
    return {
        "stage": 1,
        "total_items": 10,
        "mastered_count": 3,
        "due_count": 5,
        "new_count": 2,
        "ready_for_next_stage": False
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Actions to perform on application startup."""
    print("🚀 Flashcard Learning System API starting up...")
    print(f"📊 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔗 Database URL: {os.getenv('DATABASE_URL', 'sqlite:///./flashcard_test.db')}")
    print(f"🌐 CORS Origins: {origins}")
    print("✅ Simple SQLite auth system ready")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Actions to perform on application shutdown."""
    print("🛑 Flashcard Learning System API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
