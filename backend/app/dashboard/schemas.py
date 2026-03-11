"""
Dashboard Schemas

Pydantic models for dashboard request/response validation.
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class DashboardSummaryResponse(BaseModel):
    """Response for main dashboard summary"""
    total_elements_mastered: int
    total_reviews: int
    overall_accuracy: float
    current_streak: int
    max_streak: int
    cards_due_today: int
    active_datasets: int
    recent_badges: List[str]
    weekly_goal_progress: Optional[Dict[str, Any]] = None


class DatasetProgressResponse(BaseModel):
    """Response for individual dataset progress"""
    dataset_id: UUID
    dataset_name: str
    elements_in_dataset: int
    elements_seen: int
    elements_mastered: int
    failed_elements: int = 0  # Count of cards with failed attempts
    current_stage: int
    accuracy_rate: float
    completion_percentage: float
    status: str
    started_at: datetime
    last_studied: Optional[datetime] = None
    learning_set_id: Optional[str] = None  # Added for detailed stats


class StudySessionResponse(BaseModel):
    """Response for study session data"""
    id: UUID
    session_type: str
    cards_studied: int
    cards_correct: int
    duration_minutes: int
    accuracy_rate: float
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WeeklyGoalResponse(BaseModel):
    """Response for weekly goals"""
    id: UUID
    target_sessions_per_week: int
    target_minutes_per_week: int
    target_cards_per_week: int
    week_start_date: datetime
    sessions_completed: int
    minutes_studied: int
    cards_studied: int
    goal_achieved: bool
    streak_weeks: int
    
    class Config:
        from_attributes = True


class WeeklyGoalUpdate(BaseModel):
    """Request to update weekly goals"""
    target_sessions_per_week: Optional[int] = Field(None, ge=1, le=14)
    target_minutes_per_week: Optional[int] = Field(None, ge=10, le=1000)
    target_cards_per_week: Optional[int] = Field(None, ge=10, le=1000)


class LearningInsightResponse(BaseModel):
    """Response for learning insights"""
    id: UUID
    insight_type: str
    title: str
    message: str
    priority: str
    confidence_score: float
    is_read: bool
    is_actionable: bool
    generated_at: datetime
    
    class Config:
        from_attributes = True


class ProgressChartResponse(BaseModel):
    """Response for progress chart data"""
    dates: List[str]
    daily_reviews: List[int]
    daily_accuracy: List[float]
    cumulative_mastered: List[int]


class StudyHeatmapResponse(BaseModel):
    """Response for study activity heatmap"""
    year: int
    activity_data: Dict[str, int]  # date -> activity_count
    total_active_days: int
    max_daily_activity: int


class UserStatsResponse(BaseModel):
    """Response for detailed user statistics"""
    total_elements_seen: int
    total_elements_mastered: int
    total_reviews: int
    total_study_time_minutes: int
    overall_accuracy: float
    current_streak: int
    max_streak: int
    active_datasets: int
    completed_datasets: int
    mastery_rate: float
    learning_velocity: float
    retention_rate: float
    last_updated: datetime
    
    class Config:
        from_attributes = True


class TimeAnalyticsResponse(BaseModel):
    """Response for time-based analytics"""
    best_study_time: str  # "morning", "afternoon", "evening"
    avg_session_length: float
    total_study_time: int
    study_consistency_score: float  # 0-100
    weekly_pattern: Dict[str, int]  # day_of_week -> minutes


class PerformanceAnalyticsResponse(BaseModel):
    """Response for performance analytics"""
    accuracy_trend: List[float]  # Last 30 days
    difficult_topics: List[str]
    improvement_areas: List[str]
    strengths: List[str]
    learning_velocity: float
    retention_prediction: float


class GoalTrackingResponse(BaseModel):
    """Response for goal tracking"""
    current_week_progress: Dict[str, Any]
    monthly_summary: Dict[str, Any]
    goal_history: List[Dict[str, Any]]
    achievement_rate: float
