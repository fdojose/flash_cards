"""
Admin Schemas

Pydantic models for admin-related operations and configurations.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SystemConfigBase(BaseModel):
    key: str = Field(..., description="Configuration key identifier", max_length=100)
    value: str = Field(..., description="Configuration value as string")
    value_type: str = Field("string", description="Type of the value (string, integer, float, boolean)")
    description: Optional[str] = Field(None, description="Description of this configuration")
    category: str = Field("general", description="Category grouping for this configuration")


class SystemConfigCreate(SystemConfigBase):
    pass


class SystemConfigUpdate(BaseModel):
    value: Optional[str] = Field(None, description="New value for the configuration")
    description: Optional[str] = Field(None, description="Updated description")
    category: Optional[str] = Field(None, description="Updated category")


class SystemConfigResponse(SystemConfigBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SystemConfigBatch(BaseModel):
    configs: List[SystemConfigCreate] = Field(..., description="List of configurations to set")


class LearningConfigUpdate(BaseModel):
    """Specific schema for learning-related configurations"""
    max_set_size: Optional[int] = Field(None, ge=1, le=100, description="Maximum flashcard set size")
    initial_set_size: Optional[int] = Field(None, ge=1, le=50, description="Initial flashcard set size")
    stage_increment: Optional[int] = Field(None, ge=1, le=20, description="Size increment per stage")
    mastery_threshold: Optional[int] = Field(None, ge=1, le=10, description="Correct answers needed for mastery")
    mid_tier_threshold: Optional[int] = Field(None, ge=10, le=200, description="Threshold for mid-tier optimization")
    chunk_size_progression: Optional[str] = Field(None, description="Comma-separated chunk sizes for large dataset progression")
    reinforcement_percentage: Optional[int] = Field(None, ge=0, le=100, description="Percentage of previously learned cards for reinforcement")


class LearningConfigResponse(BaseModel):
    max_set_size: int
    initial_set_size: int
    stage_increment: int
    mastery_threshold: int
    mid_tier_threshold: int
    chunk_size_progression: str
    reinforcement_percentage: int


class RankingConfigUpdate(BaseModel):
    """Specific schema for ranking-related configurations"""
    accuracy_min_cards: Optional[int] = Field(None, ge=1, le=100, description="Minimum cards for accuracy ranking")
    speed_min_cards: Optional[int] = Field(None, ge=1, le=100, description="Minimum cards for speed ranking")
    cards_answered_min_threshold: Optional[int] = Field(None, ge=1, le=1000, description="Minimum cards answered for leaderboard")


class RankingConfigResponse(BaseModel):
    accuracy_min_cards: int
    speed_min_cards: int
    cards_answered_min_threshold: int


class SpacedRepetitionConfigUpdate(BaseModel):
    """Specific schema for spaced repetition configurations"""
    initial_ease: Optional[float] = Field(None, ge=1.0, le=10.0, description="Initial ease factor")
    minimum_ease: Optional[float] = Field(None, ge=0.5, le=5.0, description="Minimum ease factor")
    maximum_ease: Optional[float] = Field(None, ge=2.0, le=20.0, description="Maximum ease factor")
    ease_bonus: Optional[float] = Field(None, ge=0.0, le=1.0, description="Ease bonus for correct answers")
    ease_penalty: Optional[float] = Field(None, ge=0.0, le=1.0, description="Ease penalty for wrong answers")
    initial_interval: Optional[int] = Field(None, ge=1, le=30, description="Initial review interval in days")
    graduation_interval: Optional[int] = Field(None, ge=1, le=30, description="Days to graduate from learning")
    maximum_interval: Optional[int] = Field(None, ge=30, le=3650, description="Maximum days between reviews")
    learning_steps: Optional[str] = Field(None, description="Learning steps in minutes (comma-separated)")
    relearning_steps: Optional[str] = Field(None, description="Relearning steps for failed cards")


class SpacedRepetitionConfigResponse(BaseModel):
    initial_ease: float
    minimum_ease: float
    maximum_ease: float
    ease_bonus: float
    ease_penalty: float
    initial_interval: int
    graduation_interval: int
    maximum_interval: int
    learning_steps: str
    relearning_steps: str
