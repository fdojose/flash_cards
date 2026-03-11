"""
FSRS Integration Statistics Schema

Additional Pydantic models for FSRS integration statistics and detailed card information.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID


class StabilityStats(BaseModel):
    """Statistics about stability scores in the learning set"""
    average_stability: float = 0.0
    median_stability: float = 0.0
    min_stability: float = 0.0
    max_stability: float = 0.0
    high_stability_count: int = 0  # > 2.0
    medium_stability_count: int = 0  # 1.0 - 2.0
    low_stability_count: int = 0  # < 1.0


class IntegrationCardDetail(BaseModel):
    """Detailed information about a card's integration status"""
    element_id: UUID
    status: str
    integration_confirmed: bool = False
    integration_attempts: int = 0
    stability_score: float = 1.0
    last_integration_attempt: Optional[datetime] = None
    accuracy_percentage: Optional[float] = None
    review_count: int = 0
    is_difficult: bool = False


class FSRSIntegrationStats(BaseModel):
    """Comprehensive FSRS integration statistics for admin monitoring"""
    learning_set_id: UUID
    dataset_id: UUID
    user_id: UUID
    
    # Phase information
    current_phase: str  # "isolation" or "integration"
    phase_description: str
    
    # Basic counts
    total_cards: int
    mastered_count: int
    isolation_mastered_count: int
    integration_confirmed_count: int
    integration_review_count: int
    learning_count: int
    
    # Integration efficiency metrics
    integration_efficiency: float = 0.0
    first_attempt_success_rate: float = 0.0
    average_integration_attempts: float = 0.0
    reconsolidation_rate: float = 0.0  # Cards that returned to isolation
    
    # Stability metrics
    stability_stats: StabilityStats
    
    # Performance trends
    session_start_time: Optional[datetime] = None
    last_activity_time: Optional[datetime] = None
    total_session_time_minutes: Optional[float] = None
    
    # Card details (optional, for admin drill-down)
    card_details: Optional[List[IntegrationCardDetail]] = None


class IntegrationPerformanceMetrics(BaseModel):
    """System-wide FSRS integration performance metrics"""
    total_users: int
    active_integration_sessions: int
    
    # Efficiency metrics across all users
    overall_integration_efficiency: float
    overall_first_attempt_success: float
    overall_reconsolidation_rate: float
    
    # Configuration effectiveness
    current_config_hash: str  # Hash of current FSRS config for tracking changes
    config_last_updated: Optional[datetime] = None
    
    # Performance by configuration category
    high_performers: int  # > 80% integration efficiency
    medium_performers: int  # 60-80% integration efficiency
    low_performers: int  # < 60% integration efficiency
    
    # System health indicators
    error_rate: float = 0.0
    average_response_time_ms: float = 0.0
