"""
Session Schemas

Pydantic models for learning session request/response validation.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID


class SessionStartRequest(BaseModel):
    """Request to start a learning session"""
    dataset_id: UUID
    mode: Optional[str] = "progressive"  # "progressive" or "fixed"
    force_review: Optional[bool] = False  # Force review even if all cards are mastered
    # Timer settings
    timer_enabled: Optional[bool] = False
    timer_seconds: Optional[int] = 30  # Default 30 seconds
    timer_mode: Optional[str] = "optional"  # "optional", "strict", "disabled"


class SessionResponse(BaseModel):
    """Response when starting/resuming a session"""
    learning_set_id: UUID
    dataset_id: UUID
    stage: int
    status: str
    mode: str
    total_items: int
    # Chunked learning fields
    chunk_number: Optional[int] = None
    total_chunks: Optional[int] = None
    chunk_size: Optional[int] = None
    total_dataset_size: Optional[int] = None
    is_chunked_learning: bool = False
    # Learning guidance message
    learning_message: Optional[str] = None
    # Timer settings
    timer_enabled: bool = False
    timer_seconds: Optional[int] = 30
    timer_mode: Optional[str] = "optional"


class FlashcardResponse(BaseModel):
    """Response for a flashcard question"""
    element_id: UUID
    question_field: str
    question_value: str
    question_type: str
    question_media_url: Optional[str] = None
    answer_field: str
    choices: List[str]
    correct_answer: str
    # Timer information
    timer_enabled: bool = False
    timer_seconds: Optional[int] = None
    timer_mode: Optional[str] = "optional"
    # FSRS Statistics
    fsrs_stats: Optional[dict] = None


class AnswerSubmissionRequest(BaseModel):
    """Request to submit an answer"""
    element_id: UUID
    question_field: str
    answer_field: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    response_time_ms: Optional[int] = None
    # Timer information
    timer_expired: Optional[bool] = False
    was_timed: Optional[bool] = False


class AnswerSubmissionResponse(BaseModel):
    """Response after submitting an answer"""
    correct: bool
    success_streak: int
    next_due: datetime
    status: str
    explanation: str
    # Timer performance feedback
    timer_performance: Optional[str] = None  # "fast", "good", "slow", "expired"
    time_bonus: Optional[int] = 0  # Bonus points for fast answers


class ProgressResponse(BaseModel):
    """Response showing session progress with FSRS integration awareness"""
    stage: int
    total_items: int
    mastered_count: int
    due_count: int
    new_count: int
    ready_for_next_stage: bool
    
    # Confidence-based progress fields
    strong_count: int = 0          # mastered cards (status == "mastered")
    weak_count: int = 0            # learning/difficult cards  
    question_count: int = 0        # total questions answered in session
    learning_phase: str = "learning"  # "learning", "building", "mastering", "complete"
    
    # Session-level accuracy tracking
    correct_answers: int = 0       # total correct answers in current session
    total_questions: int = 0       # total questions asked in current session  
    accuracy_percentage: float = 0.0  # accuracy percentage for current session
    
    # FSRS Integration-specific fields
    isolation_mastered_count: int = 0  # Cards mastered in isolation but not integration-confirmed
    integration_confirmed_count: int = 0  # Cards confirmed in integration phase
    integration_review_count: int = 0  # Cards needing integration re-confirmation
    phase_description: str = ""  # Human-readable phase description
    integration_efficiency: float = 0.0  # Percentage of cards confirmed on first integration attempt
    
    # Stability scoring metrics
    average_stability_score: float = 0.0  # Average stability of confirmed cards
    high_stability_count: int = 0  # Cards with stability > 2.0
    low_stability_count: int = 0  # Cards with stability < 1.0


class ReviewSummary(BaseModel):
    """Summary of review data for an element"""
    element_id: UUID
    success_streak: int
    review_count: int
    status: str
    last_reviewed: Optional[datetime] = None
    next_due: Optional[datetime] = None
    is_difficult: bool
