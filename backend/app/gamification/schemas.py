"""
Gamification Schemas

Pydantic models for gamification request/response validation.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID


class BadgeResponse(BaseModel):
    """Response for user badge information"""
    id: UUID
    achievement_title: str
    achievement_description: Optional[str] = None
    badge_emoji: Optional[str] = None
    date_awarded: datetime

    class Config:
        from_attributes = True


class StreakResponse(BaseModel):
    """Response for user streak information"""
    current_streak: int
    max_streak: int
    last_activity: Optional[datetime] = None
    streak_type: str
    
    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    """Individual leaderboard entry"""
    rank: int
    user_id: UUID
    user_name: str
    value: int
    is_current_user: bool


class LeaderboardResponse(BaseModel):
    """Response for leaderboard data"""
    score_type: str
    period: str
    dataset_id: Optional[str] = None
    entries: List[LeaderboardEntry]


class BadgeCreateRequest(BaseModel):
    """Request to create/award a badge"""
    user_id: UUID
    badge_name: str
    description: Optional[str] = None
    icon: Optional[str] = None


class ScoreUpdateRequest(BaseModel):
    """Request to update leaderboard score"""
    user_id: UUID
    dataset_id: Optional[UUID] = None
    score_type: str
    value: int
    period: str = "all_time"


class BadgeDefinitionResponse(BaseModel):
    """Response for badge definition"""
    id: UUID
    name: str
    description: str
    icon: Optional[str] = None
    criteria_type: str
    criteria_value: int
    is_active: bool
    
    class Config:
        from_attributes = True
