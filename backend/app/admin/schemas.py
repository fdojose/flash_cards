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
    mid_tier_threshold: Optional[int] = Field(None, ge=10, le=200, description="Threshold for mid-tier optimization")
    chunk_size_progression: Optional[str] = Field(None, description="Comma-separated chunk sizes for large dataset progression")
    reinforcement_percentage: Optional[int] = Field(None, ge=0, le=100, description="Percentage of previously learned cards for reinforcement")


class IntegrationConfigUpdate(BaseModel):
    """FSRS Integration Configuration Schema with full validation"""
    # FSRS Integration Variables
    integration_enhancement_enabled: Optional[bool] = Field(None, description="Master switch for FSRS integration enhancement")
    integration_confirmation_threshold: Optional[float] = Field(None, ge=0.7, le=1.0, description="Accuracy required for integration confirmation")
    integration_max_attempts: Optional[int] = Field(None, ge=2, le=5, description="Max attempts before returning to isolation")
    stability_boost_factor: Optional[float] = Field(None, ge=1.1, le=1.5, description="Stability multiplier on success")
    stability_decay_factor: Optional[float] = Field(None, ge=0.6, le=0.9, description="Stability multiplier on failure")
    stability_max_score: Optional[float] = Field(None, ge=2.0, le=5.0, description="Maximum stability score cap")
    integration_failure_penalty: Optional[float] = Field(None, ge=0.7, le=0.95, description="Stability penalty for confirmed card failure")
    reconsolidation_threshold: Optional[int] = Field(None, ge=1, le=3, description="Failures before triggering reconsolidation")
    stability_maintenance_boost: Optional[float] = Field(None, ge=1.01, le=1.1, description="Stability boost for confirmed cards on success")
    
    # Mastery Window Variables  
    default_mastery_window: Optional[int] = Field(None, ge=2, le=5, description="Default mastery window when field count unavailable")
    isolation_min_mastery_window: Optional[int] = Field(None, ge=1, le=3, description="Minimum mastery window in isolation phase")
    isolation_max_mastery_window: Optional[int] = Field(None, ge=5, le=12, description="Maximum mastery window in isolation phase")
    isolation_field_multiplier: Optional[float] = Field(None, ge=1.2, le=2.0, description="Field count multiplier for large cards")
    single_field_mastery_window: Optional[int] = Field(None, ge=1, le=3, description="Mastery window for single-field cards")
    two_field_mastery_window: Optional[int] = Field(None, ge=2, le=4, description="Mastery window for two-field cards")
    integration_mastery_window: Optional[int] = Field(None, ge=1, le=2, description="Mastery window for integration phase")
    required_mastery_window: Optional[int] = Field(None, ge=2, le=5, description="Required window for isolation mastery calculation")
    isolation_mastery_percentage: Optional[float] = Field(None, ge=0.6, le=1.0, description="Accuracy threshold for isolation mastery")
    initial_stability_score: Optional[float] = Field(None, ge=0.5, le=2.0, description="Initial stability score for newly mastered cards")


class IntegrationConfigResponse(BaseModel):
    """FSRS Integration Configuration Response"""
    # FSRS Integration Variables
    integration_enhancement_enabled: bool
    integration_confirmation_threshold: float
    integration_max_attempts: int
    stability_boost_factor: float
    stability_decay_factor: float
    stability_max_score: float
    integration_failure_penalty: float
    reconsolidation_threshold: int
    stability_maintenance_boost: float
    
    # Mastery Window Variables
    default_mastery_window: int
    isolation_min_mastery_window: int
    isolation_max_mastery_window: int
    isolation_field_multiplier: float
    single_field_mastery_window: int
    two_field_mastery_window: int
    integration_mastery_window: int
    required_mastery_window: int
    isolation_mastery_percentage: float
    initial_stability_score: float
    
    class Config:
        from_attributes = True


class LearningConfigResponse(BaseModel):
    max_set_size: int
    initial_set_size: int
    stage_increment: int
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


class SpiralConfigUpdate(BaseModel):
    """Spiral Learning Configuration Schema with validation"""
    spiral_learning_enabled: Optional[bool] = Field(None, description="Enable spiral learning comprehensive reviews")
    spiral_review_trigger_interval: Optional[int] = Field(None, ge=1, le=5, description="Number of integration cycles before triggering spiral review")
    spiral_review_max_cards: Optional[int] = Field(None, ge=5, le=50, description="Maximum number of cards in a spiral review session")
    spiral_weakness_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Accuracy threshold below which cards are considered weak")
    spiral_stability_threshold: Optional[float] = Field(None, ge=0.5, le=5.0, description="Stability threshold below which cards are considered weak")
    spiral_integration_failure_weight: Optional[float] = Field(None, ge=1.0, le=10.0, description="Weight multiplier for cards with integration failures")


class SpiralConfigResponse(BaseModel):
    """Spiral Learning Configuration Response"""
    spiral_learning_enabled: bool = Field(description="Enable spiral learning comprehensive reviews")
    spiral_review_trigger_interval: int = Field(description="Number of integration cycles before triggering spiral review")
    spiral_review_max_cards: int = Field(description="Maximum number of cards in a spiral review session")
    spiral_weakness_threshold: float = Field(description="Accuracy threshold below which cards are considered weak")
    spiral_stability_threshold: float = Field(description="Stability threshold below which cards are considered weak")
    spiral_integration_failure_weight: float = Field(description="Weight multiplier for cards with integration failures")
    
    class Config:
        from_attributes = True
