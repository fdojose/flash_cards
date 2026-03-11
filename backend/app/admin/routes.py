"""
Admin Routes

API endpoints for system administration and configuration management.
Requires admin role for access.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

# Database and auth dependencies
from ..database import get_db
from ..auth.routes import get_admin_user
from ..auth.models import User

# Models and schemas
from .models import SystemConfig
from .schemas import (
    SystemConfigResponse, SystemConfigCreate, SystemConfigUpdate, 
    SystemConfigBatch, LearningConfigUpdate, LearningConfigResponse,
    RankingConfigUpdate, RankingConfigResponse,
    IntegrationConfigResponse, IntegrationConfigUpdate,
    SpiralConfigResponse, SpiralConfigUpdate
)
from ..sessions.fsrs_schemas import IntegrationPerformanceMetrics

# Import for dynamic mastery window calculation
from ..sessions.routes import get_dynamic_mastery_window
from ..datasets.models import Dataset

router = APIRouter(prefix="/admin", tags=["admin"])


# Default learning configuration values
DEFAULT_LEARNING_CONFIG = {
    "max_set_size": {"value": 30, "type": "integer", "description": "Maximum flashcard set size", "category": "learning"},
    "initial_set_size": {"value": 10, "type": "integer", "description": "Initial flashcard set size", "category": "learning"},
    "stage_increment": {"value": 10, "type": "integer", "description": "Size increment per stage", "category": "learning"},
    "mid_tier_threshold": {"value": 80, "type": "integer", "description": "Threshold for mid-tier optimization (datasets with 16-80 cards)", "category": "learning"},
    "chunk_size_progression": {"value": "100,75,60,50", "type": "string", "description": "Comma-separated list of chunk sizes for large dataset progression", "category": "learning"},
    "reinforcement_percentage": {"value": 10, "type": "integer", "description": "Percentage of previously learned cards to include for reinforcement", "category": "learning"},
    
    # Staged Isolation Learning Configuration
    "batch_size": {"value": 5, "type": "integer", "description": "Size of each learning batch in staged isolation", "category": "learning"},
    "isolation_mastery_percentage": {"value": 0.8, "type": "float", "description": "Accuracy percentage required in isolation phase (80%)", "category": "learning"},
    "integration_mastery_percentage": {"value": 0.7, "type": "float", "description": "Accuracy percentage required in integration phase (70%)", "category": "learning"},
    "mastery_review_window": {"value": 10, "type": "integer", "description": "Number of recent attempts to consider for mastery calculation", "category": "learning"},
    
    # Spiral Learning Configuration
    "spiral_learning_enabled": {"value": True, "type": "boolean", "description": "Enable spiral learning comprehensive reviews", "category": "spiral_learning"},
    "spiral_review_trigger_interval": {"value": 2, "type": "integer", "description": "Number of integration cycles before triggering spiral review", "category": "spiral_learning"},
    "spiral_review_max_cards": {"value": 20, "type": "integer", "description": "Maximum number of cards in a spiral review session", "category": "spiral_learning"},
    "spiral_weakness_threshold": {"value": 0.6, "type": "float", "description": "Accuracy threshold below which cards are considered weak", "category": "spiral_learning"},
    "spiral_stability_threshold": {"value": 1.5, "type": "float", "description": "Stability threshold below which cards are considered weak", "category": "spiral_learning"},
    "spiral_integration_failure_weight": {"value": 2.0, "type": "float", "description": "Weight multiplier for cards with integration failures", "category": "spiral_learning"}
}

# Default ranking configuration values  
DEFAULT_RANKING_CONFIG = {
    "accuracy_min_cards": {"value": 5, "type": "integer", "description": "Minimum cards answered for accuracy ranking", "category": "ranking"},
    "speed_min_cards": {"value": 10, "type": "integer", "description": "Minimum cards answered for speed ranking", "category": "ranking"},
    "cards_answered_min_threshold": {"value": 20, "type": "integer", "description": "Minimum cards answered for leaderboard appearance", "category": "ranking"}
}

# Default spaced repetition configuration values
DEFAULT_SPACED_REPETITION_CONFIG = {
    "initial_ease": {"value": 2.5, "type": "float", "description": "Initial ease factor for new cards in spaced repetition (SM-2 algorithm)", "category": "spaced_repetition"},
    "minimum_ease": {"value": 1.3, "type": "float", "description": "Minimum ease factor (floor value for difficult cards)", "category": "spaced_repetition"},
    "maximum_ease": {"value": 5.0, "type": "float", "description": "Maximum ease factor (ceiling value for easy cards)", "category": "spaced_repetition"},
    "ease_bonus": {"value": 0.15, "type": "float", "description": "Ease factor bonus added for correct answers", "category": "spaced_repetition"},
    "ease_penalty": {"value": 0.2, "type": "float", "description": "Ease factor penalty subtracted for wrong answers", "category": "spaced_repetition"},
    "initial_interval": {"value": 1, "type": "integer", "description": "Initial review interval in days for new cards", "category": "spaced_repetition"},
    "graduation_interval": {"value": 4, "type": "integer", "description": "Days to graduate from learning phase to review phase", "category": "spaced_repetition"},
    "maximum_interval": {"value": 365, "type": "integer", "description": "Maximum days between reviews", "category": "spaced_repetition"},
    "learning_steps": {"value": "1,10,1440", "type": "string", "description": "Learning steps in minutes (comma-separated: 1min, 10min, 1day)", "category": "spaced_repetition"},
    "relearning_steps": {"value": "10,1440", "type": "string", "description": "Relearning steps in minutes for failed cards (10min, 1day)", "category": "spaced_repetition"}
}

# Default FSRS integration configuration values
DEFAULT_INTEGRATION_CONFIG = {
    # FSRS Integration Variables
    "integration_enhancement_enabled": {"value": True, "type": "boolean", "description": "Master switch for FSRS integration enhancement", "category": "fsrs_integration"},
    "integration_confirmation_threshold": {"value": 0.8, "type": "float", "description": "Accuracy required for integration confirmation", "category": "fsrs_integration"},
    "integration_max_attempts": {"value": 3, "type": "integer", "description": "Max attempts before returning to isolation", "category": "fsrs_integration"},
    "stability_boost_factor": {"value": 1.2, "type": "float", "description": "Stability multiplier on success", "category": "fsrs_integration"},
    "stability_decay_factor": {"value": 0.8, "type": "float", "description": "Stability multiplier on failure", "category": "fsrs_integration"},
    "stability_max_score": {"value": 3.0, "type": "float", "description": "Maximum stability score cap", "category": "fsrs_integration"},
    "integration_failure_penalty": {"value": 0.85, "type": "float", "description": "Stability penalty for confirmed card failure", "category": "fsrs_integration"},
    "reconsolidation_threshold": {"value": 2, "type": "integer", "description": "Failures before triggering reconsolidation", "category": "fsrs_integration"},
    "stability_maintenance_boost": {"value": 1.05, "type": "float", "description": "Stability boost for confirmed cards on success", "category": "fsrs_integration"},
    
    # Mastery Window Variables
    "default_mastery_window": {"value": 3, "type": "integer", "description": "Default mastery window when field count unavailable", "category": "fsrs_mastery"},
    "isolation_min_mastery_window": {"value": 2, "type": "integer", "description": "Minimum mastery window in isolation phase", "category": "fsrs_mastery"},
    "isolation_max_mastery_window": {"value": 8, "type": "integer", "description": "Maximum mastery window in isolation phase", "category": "fsrs_mastery"},
    "isolation_field_multiplier": {"value": 1.5, "type": "float", "description": "Field count multiplier for large cards", "category": "fsrs_mastery"},
    "single_field_mastery_window": {"value": 2, "type": "integer", "description": "Mastery window for single-field cards", "category": "fsrs_mastery"},
    "two_field_mastery_window": {"value": 3, "type": "integer", "description": "Mastery window for two-field cards", "category": "fsrs_mastery"},
    "integration_mastery_window": {"value": 2, "type": "integer", "description": "Mastery window for integration phase", "category": "fsrs_mastery"},
    "required_mastery_window": {"value": 3, "type": "integer", "description": "Required window for isolation mastery calculation", "category": "fsrs_mastery"},
    "isolation_mastery_percentage": {"value": 0.75, "type": "float", "description": "Accuracy threshold for isolation mastery", "category": "fsrs_mastery"},
    "initial_stability_score": {"value": 1.0, "type": "float", "description": "Initial stability score for newly mastered cards", "category": "fsrs_mastery"}
}


@router.get("/config", response_model=List[SystemConfigResponse])
async def get_all_configs(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Get all system configurations (admin only)"""
    query = db.query(SystemConfig)
    if category:
        query = query.filter(SystemConfig.category == category)
    
    configs = query.all()
    return configs


@router.get("/config/learning", response_model=LearningConfigResponse)
async def get_learning_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Get learning-specific configuration settings (admin only)"""
    # Initialize default values if they don't exist
    await initialize_learning_config(db)
    
    return LearningConfigResponse(
        max_set_size=SystemConfig.get_value(db, "max_set_size", 30),
        initial_set_size=SystemConfig.get_value(db, "initial_set_size", 10),
        stage_increment=SystemConfig.get_value(db, "stage_increment", 10),
        mid_tier_threshold=SystemConfig.get_value(db, "mid_tier_threshold", 80),
        chunk_size_progression=SystemConfig.get_value(db, "chunk_size_progression", "100,75,60,50"),
        reinforcement_percentage=SystemConfig.get_value(db, "reinforcement_percentage", 10)
    )


@router.put("/config/learning", response_model=LearningConfigResponse)
async def update_learning_config(
    config_data: LearningConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Update learning-specific configuration settings (admin only)"""
    # Update each provided configuration
    if config_data.max_set_size is not None:
        SystemConfig.set_value(
            db, "max_set_size", config_data.max_set_size, "integer",
            "Maximum flashcard set size", "learning"
        )
    
    if config_data.initial_set_size is not None:
        SystemConfig.set_value(
            db, "initial_set_size", config_data.initial_set_size, "integer",
            "Initial flashcard set size", "learning"
        )
    
    if config_data.stage_increment is not None:
        SystemConfig.set_value(
            db, "stage_increment", config_data.stage_increment, "integer",
            "Size increment per stage", "learning"
        )
    
    return await get_learning_config(db, current_user)


@router.get("/config/ranking", response_model=RankingConfigResponse)
async def get_ranking_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Get ranking-specific configuration settings (admin only)"""
    # Initialize default values if they don't exist
    await initialize_ranking_config(db)
    
    return RankingConfigResponse(
        accuracy_min_cards=SystemConfig.get_value(db, "accuracy_min_cards", 5),
        speed_min_cards=SystemConfig.get_value(db, "speed_min_cards", 10),
        cards_answered_min_threshold=SystemConfig.get_value(db, "cards_answered_min_threshold", 20)
    )


@router.put("/config/ranking", response_model=RankingConfigResponse)
async def update_ranking_config(
    config_data: RankingConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Update ranking-specific configuration settings (admin only)"""
    # Update each provided configuration
    if config_data.accuracy_min_cards is not None:
        SystemConfig.set_value(
            db, "accuracy_min_cards", config_data.accuracy_min_cards, "integer",
            "Minimum cards answered for accuracy ranking", "ranking"
        )
    
    if config_data.speed_min_cards is not None:
        SystemConfig.set_value(
            db, "speed_min_cards", config_data.speed_min_cards, "integer", 
            "Minimum cards answered for speed ranking", "ranking"
        )
    
    if config_data.cards_answered_min_threshold is not None:
        SystemConfig.set_value(
            db, "cards_answered_min_threshold", config_data.cards_answered_min_threshold, "integer",
            "Minimum cards answered for leaderboard appearance", "ranking"
        )
    
    return await get_ranking_config(db, current_user)


@router.get("/config/integration", response_model=IntegrationConfigResponse)
async def get_integration_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Get FSRS integration configuration settings (admin only)"""
    # Initialize default values if they don't exist
    await initialize_integration_config(db)
    
    return IntegrationConfigResponse(
        # FSRS Integration Variables
        integration_enhancement_enabled=SystemConfig.get_value(db, "integration_enhancement_enabled", True),
        integration_confirmation_threshold=SystemConfig.get_value(db, "integration_confirmation_threshold", 0.8),
        integration_max_attempts=SystemConfig.get_value(db, "integration_max_attempts", 3),
        stability_boost_factor=SystemConfig.get_value(db, "stability_boost_factor", 1.2),
        stability_decay_factor=SystemConfig.get_value(db, "stability_decay_factor", 0.8),
        stability_max_score=SystemConfig.get_value(db, "stability_max_score", 3.0),
        integration_failure_penalty=SystemConfig.get_value(db, "integration_failure_penalty", 0.85),
        reconsolidation_threshold=SystemConfig.get_value(db, "reconsolidation_threshold", 2),
        stability_maintenance_boost=SystemConfig.get_value(db, "stability_maintenance_boost", 1.05),
        
        # Mastery Window Variables
        default_mastery_window=SystemConfig.get_value(db, "default_mastery_window", 3),
        isolation_min_mastery_window=SystemConfig.get_value(db, "isolation_min_mastery_window", 2),
        isolation_max_mastery_window=SystemConfig.get_value(db, "isolation_max_mastery_window", 8),
        isolation_field_multiplier=SystemConfig.get_value(db, "isolation_field_multiplier", 1.5),
        single_field_mastery_window=SystemConfig.get_value(db, "single_field_mastery_window", 2),
        two_field_mastery_window=SystemConfig.get_value(db, "two_field_mastery_window", 3),
        integration_mastery_window=SystemConfig.get_value(db, "integration_mastery_window", 2),
        required_mastery_window=SystemConfig.get_value(db, "required_mastery_window", 3),
        isolation_mastery_percentage=SystemConfig.get_value(db, "isolation_mastery_percentage", 0.75),
        initial_stability_score=SystemConfig.get_value(db, "initial_stability_score", 1.0)
    )


@router.put("/config/integration", response_model=IntegrationConfigResponse)
async def update_integration_config(
    config_data: IntegrationConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Update FSRS integration configuration settings (admin only)"""
    # Update FSRS Integration Variables
    if config_data.integration_enhancement_enabled is not None:
        SystemConfig.set_value(
            db, "integration_enhancement_enabled", config_data.integration_enhancement_enabled, "boolean",
            "Master switch for FSRS integration enhancement", "fsrs_integration"
        )
    
    if config_data.integration_confirmation_threshold is not None:
        SystemConfig.set_value(
            db, "integration_confirmation_threshold", config_data.integration_confirmation_threshold, "float",
            "Accuracy required for integration confirmation", "fsrs_integration"
        )
    
    if config_data.integration_max_attempts is not None:
        SystemConfig.set_value(
            db, "integration_max_attempts", config_data.integration_max_attempts, "integer",
            "Max attempts before returning to isolation", "fsrs_integration"
        )
    
    if config_data.stability_boost_factor is not None:
        SystemConfig.set_value(
            db, "stability_boost_factor", config_data.stability_boost_factor, "float",
            "Stability multiplier on success", "fsrs_integration"
        )
    
    if config_data.stability_decay_factor is not None:
        SystemConfig.set_value(
            db, "stability_decay_factor", config_data.stability_decay_factor, "float",
            "Stability multiplier on failure", "fsrs_integration"
        )
    
    if config_data.stability_max_score is not None:
        SystemConfig.set_value(
            db, "stability_max_score", config_data.stability_max_score, "float",
            "Maximum stability score cap", "fsrs_integration"
        )
    
    if config_data.integration_failure_penalty is not None:
        SystemConfig.set_value(
            db, "integration_failure_penalty", config_data.integration_failure_penalty, "float",
            "Stability penalty for confirmed card failure", "fsrs_integration"
        )
    
    if config_data.reconsolidation_threshold is not None:
        SystemConfig.set_value(
            db, "reconsolidation_threshold", config_data.reconsolidation_threshold, "integer",
            "Failures before triggering reconsolidation", "fsrs_integration"
        )
    
    if config_data.stability_maintenance_boost is not None:
        SystemConfig.set_value(
            db, "stability_maintenance_boost", config_data.stability_maintenance_boost, "float",
            "Stability boost for confirmed cards on success", "fsrs_integration"
        )
    
    # Update Mastery Window Variables
    if config_data.default_mastery_window is not None:
        SystemConfig.set_value(
            db, "default_mastery_window", config_data.default_mastery_window, "integer",
            "Default mastery window when field count unavailable", "fsrs_mastery"
        )
    
    if config_data.isolation_min_mastery_window is not None:
        SystemConfig.set_value(
            db, "isolation_min_mastery_window", config_data.isolation_min_mastery_window, "integer",
            "Minimum mastery window in isolation phase", "fsrs_mastery"
        )
    
    if config_data.isolation_max_mastery_window is not None:
        SystemConfig.set_value(
            db, "isolation_max_mastery_window", config_data.isolation_max_mastery_window, "integer",
            "Maximum mastery window in isolation phase", "fsrs_mastery"
        )
    
    if config_data.isolation_field_multiplier is not None:
        SystemConfig.set_value(
            db, "isolation_field_multiplier", config_data.isolation_field_multiplier, "float",
            "Field count multiplier for large cards", "fsrs_mastery"
        )
    
    if config_data.single_field_mastery_window is not None:
        SystemConfig.set_value(
            db, "single_field_mastery_window", config_data.single_field_mastery_window, "integer",
            "Mastery window for single-field cards", "fsrs_mastery"
        )
    
    if config_data.two_field_mastery_window is not None:
        SystemConfig.set_value(
            db, "two_field_mastery_window", config_data.two_field_mastery_window, "integer",
            "Mastery window for two-field cards", "fsrs_mastery"
        )
    
    if config_data.integration_mastery_window is not None:
        SystemConfig.set_value(
            db, "integration_mastery_window", config_data.integration_mastery_window, "integer",
            "Mastery window for integration phase", "fsrs_mastery"
        )
    
    if config_data.required_mastery_window is not None:
        SystemConfig.set_value(
            db, "required_mastery_window", config_data.required_mastery_window, "integer",
            "Required window for isolation mastery calculation", "fsrs_mastery"
        )
    
    if config_data.isolation_mastery_percentage is not None:
        SystemConfig.set_value(
            db, "isolation_mastery_percentage", config_data.isolation_mastery_percentage, "float",
            "Accuracy threshold for isolation mastery", "fsrs_mastery"
        )
    
    if config_data.initial_stability_score is not None:
        SystemConfig.set_value(
            db, "initial_stability_score", config_data.initial_stability_score, "float",
            "Initial stability score for newly mastered cards", "fsrs_mastery"
        )
    
    return await get_integration_config(db, current_user)


@router.get("/config/{key}", response_model=SystemConfigResponse)
async def get_config(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Get a specific configuration by key (admin only)"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration '{key}' not found"
        )
    return config


@router.post("/config", response_model=SystemConfigResponse)
async def create_or_update_config(
    config_data: SystemConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Create or update a system configuration (admin only)"""
    config = SystemConfig.set_value(
        db=db,
        key=config_data.key,
        value=config_data.value,
        value_type=config_data.value_type,
        description=config_data.description,
        category=config_data.category
    )
    return config


@router.put("/config/{key}", response_model=SystemConfigResponse)
async def update_config(
    key: str,
    config_data: SystemConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Update an existing configuration (admin only)"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration '{key}' not found"
        )
    
    if config_data.value is not None:
        config.value = config_data.value
    if config_data.description is not None:
        config.description = config_data.description
    if config_data.category is not None:
        config.category = config_data.category
    
    db.commit()
    db.refresh(config)
    return config


@router.delete("/config/{key}")
async def delete_config(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Delete a configuration (admin only)"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration '{key}' not found"
        )
    
    db.delete(config)
    db.commit()
    return {"message": f"Configuration '{key}' deleted successfully"}


@router.post("/config/batch", response_model=List[SystemConfigResponse])
async def set_batch_configs(
    batch_data: SystemConfigBatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Set multiple configurations at once (admin only)"""
    results = []
    for config_data in batch_data.configs:
        config = SystemConfig.set_value(
            db=db,
            key=config_data.key,
            value=config_data.value,
            value_type=config_data.value_type,
            description=config_data.description,
            category=config_data.category
        )
        results.append(config)
    return results


async def initialize_learning_config(db: Session):
    """Initialize default learning configuration if not exists"""
    for key, config in DEFAULT_LEARNING_CONFIG.items():
        existing = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if not existing:
            SystemConfig.set_value(
                db=db,
                key=key,
                value=config["value"],
                value_type=config["type"],
                description=config["description"],
                category=config["category"]
            )


async def initialize_ranking_config(db: Session):
    """Initialize default ranking configuration if not exists"""
    for key, config in DEFAULT_RANKING_CONFIG.items():
        existing = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if not existing:
            SystemConfig.set_value(
                db=db,
                key=key,
                value=config["value"],
                value_type=config["type"],
                description=config["description"],
                category=config["category"]
            )


async def initialize_spaced_repetition_config(db: Session):
    """Initialize default spaced repetition configuration if not exists"""
    for key, config in DEFAULT_SPACED_REPETITION_CONFIG.items():
        existing = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if not existing:
            SystemConfig.set_value(
                db=db,
                key=key,
                value=config["value"],
                value_type=config["type"],
                description=config["description"],
                category=config["category"]
            )


async def initialize_integration_config(db: Session):
    """Initialize default FSRS integration configuration if not exists"""
    for key, config in DEFAULT_INTEGRATION_CONFIG.items():
        existing = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if not existing:
            SystemConfig.set_value(
                db=db,
                key=key,
                value=config["value"],
                value_type=config["type"],
                description=config["description"],
                category=config["category"]
            )
        if not existing:
            SystemConfig.set_value(
                db=db,
                key=key,
                value=config["value"],
                value_type=config["type"],
                description=config["description"],
                category=config["category"]
            )


@router.post("/config/learning/reset")
async def reset_learning_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Reset learning configuration to default values (admin only)"""
    for key, config in DEFAULT_LEARNING_CONFIG.items():
        SystemConfig.set_value(
            db=db,
            key=key,
            value=config["value"],
            value_type=config["type"],
            description=config["description"],
            category=config["category"]
        )
    
    return await get_learning_config(db, current_user)


@router.post("/config/ranking/reset")
async def reset_ranking_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Reset ranking configuration to default values (admin only)"""
    for key, config in DEFAULT_RANKING_CONFIG.items():
        SystemConfig.set_value(
            db=db,
            key=key,
            value=config["value"],
            value_type=config["type"],
            description=config["description"],
            category=config["category"]
        )
    
    return await get_ranking_config(db, current_user)


@router.get("/config/learning/public", response_model=LearningConfigResponse)
async def get_learning_config_public(
    db: Session = Depends(get_db)
):
    """Get learning-specific configuration settings (public endpoint for display purposes)"""
    # Initialize default values if they don't exist
    await initialize_learning_config(db)
    
    return LearningConfigResponse(
        max_set_size=SystemConfig.get_value(db, "max_set_size", 30),
        initial_set_size=SystemConfig.get_value(db, "initial_set_size", 10),
        stage_increment=SystemConfig.get_value(db, "stage_increment", 10),
        mid_tier_threshold=SystemConfig.get_value(db, "mid_tier_threshold", 80),
        chunk_size_progression=SystemConfig.get_value(db, "chunk_size_progression", "100,75,60,50"),
        reinforcement_percentage=SystemConfig.get_value(db, "reinforcement_percentage", 10),
        batch_size=SystemConfig.get_value(db, "batch_size", 5),
        isolation_mastery_percentage=SystemConfig.get_value(db, "isolation_mastery_percentage", 0.8),
        integration_mastery_percentage=SystemConfig.get_value(db, "integration_mastery_percentage", 0.7),
        mastery_review_window=SystemConfig.get_value(db, "mastery_review_window", 10)
    )


@router.get("/datasets/mastery-info")
async def get_datasets_mastery_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Get dynamic mastery window information for all datasets"""
    datasets = db.query(Dataset).filter(Dataset.is_active == True).all()
    
    mastery_info = []
    static_window = SystemConfig.get_value(db, "mastery_review_window", 10)
    
    for dataset in datasets:
        dynamic_window = get_dynamic_mastery_window(db, str(dataset.id))
        
        mastery_info.append({
            "dataset_id": str(dataset.id),
            "dataset_name": dataset.name,
            "static_mastery_window": static_window,
            "dynamic_mastery_window": dynamic_window,
            "improvement": static_window - dynamic_window,
            "efficiency_gain": f"{((static_window - dynamic_window) / static_window * 100):.0f}%" if dynamic_window < static_window else "0%"
        })
    
    return {
        "datasets": mastery_info,
        "system_note": "Research-optimized mastery: 2-field cards=3 attempts (initial+reverse+confirmation), multi-field=field_count+1, max=8",
        "benefit": "Cards reach mastery 70% faster using spaced learning research principles"
    }


@router.get("/fsrs-performance", response_model=IntegrationPerformanceMetrics)
async def get_fsrs_performance_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Get system-wide FSRS integration performance metrics (admin only)"""
    from ..sessions.models import UserLearningSet, UserElementReview
    from ..auth.models import User
    import hashlib
    import json
    
    # Get overall user statistics
    total_users = db.query(User).count()
    active_integration_sessions = db.query(UserLearningSet).filter(
        UserLearningSet.isolation_phase == False
    ).count()
    
    # Get all reviews with integration data
    integration_reviews = db.query(UserElementReview).filter(
        UserElementReview.integration_attempts > 0
    ).all()
    
    if not integration_reviews:
        # No integration data available yet
        return IntegrationPerformanceMetrics(
            total_users=total_users,
            active_integration_sessions=active_integration_sessions,
            overall_integration_efficiency=0.0,
            overall_first_attempt_success=0.0,
            overall_reconsolidation_rate=0.0,
            current_config_hash="",
            high_performers=0,
            medium_performers=0,
            low_performers=0
        )
    
    # Calculate system-wide integration efficiency
    successful_first_attempts = len([r for r in integration_reviews 
                                   if r.integration_confirmed and r.integration_attempts == 1])
    overall_integration_efficiency = (successful_first_attempts / len(integration_reviews) * 100)
    overall_first_attempt_success = overall_integration_efficiency
    
    # Calculate reconsolidation rate
    reconsolidated_cards = len([r for r in integration_reviews 
                               if r.integration_attempts >= 3 and r.status == "learning"])
    overall_reconsolidation_rate = (reconsolidated_cards / len(integration_reviews) * 100)
    
    # Get current configuration hash for tracking changes
    fsrs_configs = db.query(SystemConfig).filter(
        SystemConfig.category.in_(["fsrs_integration", "fsrs_mastery"])
    ).all()
    
    config_data = {config.key: config.value for config in fsrs_configs}
    config_json = json.dumps(config_data, sort_keys=True)
    current_config_hash = hashlib.md5(config_json.encode()).hexdigest()[:8]
    
    # Get configuration last updated timestamp
    config_last_updated = None
    if fsrs_configs:
        config_last_updated = max([config.updated_at for config in fsrs_configs if config.updated_at])
    
    # Calculate user performance categories
    # For this, we'd need to group by user and calculate individual efficiencies
    user_reviews = {}
    for review in integration_reviews:
        if review.user_id not in user_reviews:
            user_reviews[review.user_id] = []
        user_reviews[review.user_id].append(review)
    
    high_performers = medium_performers = low_performers = 0
    
    for user_id, reviews in user_reviews.items():
        user_successful_first = len([r for r in reviews 
                                   if r.integration_confirmed and r.integration_attempts == 1])
        user_efficiency = (user_successful_first / len(reviews) * 100) if reviews else 0
        
        if user_efficiency > 80:
            high_performers += 1
        elif user_efficiency >= 60:
            medium_performers += 1
        else:
            low_performers += 1
    
    return IntegrationPerformanceMetrics(
        total_users=total_users,
        active_integration_sessions=active_integration_sessions,
        overall_integration_efficiency=round(overall_integration_efficiency, 1),
        overall_first_attempt_success=round(overall_first_attempt_success, 1),
        overall_reconsolidation_rate=round(overall_reconsolidation_rate, 1),
        current_config_hash=current_config_hash,
        config_last_updated=config_last_updated,
        high_performers=high_performers,
        medium_performers=medium_performers,
        low_performers=low_performers,
        error_rate=0.0,  # Would need error tracking system
        average_response_time_ms=0.0  # Would need performance monitoring
    )


# Spiral Learning Configuration Endpoints

@router.get("/config/spiral", response_model=SpiralConfigResponse)
async def get_spiral_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Get spiral learning configuration settings (admin only)"""
    
    # Initialize default spiral learning values if they don't exist
    spiral_defaults = {
        "spiral_learning_enabled": True,
        "spiral_review_trigger_interval": 2,
        "spiral_review_max_cards": 20,
        "spiral_weakness_threshold": 0.6,
        "spiral_stability_threshold": 1.5,
        "spiral_integration_failure_weight": 2.0
    }
    
    for key, default_value in spiral_defaults.items():
        if not db.query(SystemConfig).filter(SystemConfig.key == key).first():
            value_type = "boolean" if isinstance(default_value, bool) else "float" if isinstance(default_value, float) else "integer"
            SystemConfig.set_value(
                db=db,
                key=key,
                value=default_value,
                value_type=value_type,
                description=f"Spiral learning configuration: {key.replace('_', ' ').title()}",
                category="spiral_learning"
            )
    
    return SpiralConfigResponse(
        spiral_learning_enabled=SystemConfig.get_value(db, "spiral_learning_enabled", True),
        spiral_review_trigger_interval=SystemConfig.get_value(db, "spiral_review_trigger_interval", 2),
        spiral_review_max_cards=SystemConfig.get_value(db, "spiral_review_max_cards", 20),
        spiral_weakness_threshold=SystemConfig.get_value(db, "spiral_weakness_threshold", 0.6),
        spiral_stability_threshold=SystemConfig.get_value(db, "spiral_stability_threshold", 1.5),
        spiral_integration_failure_weight=SystemConfig.get_value(db, "spiral_integration_failure_weight", 2.0)
    )


@router.put("/config/spiral", response_model=SpiralConfigResponse)
async def update_spiral_config(
    config: SpiralConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Update spiral learning configuration settings (admin only)"""
    
    updates = {}
    
    for field, value in config.dict(exclude_unset=True).items():
        if value is not None:
            # Determine value type
            value_type = "boolean" if isinstance(value, bool) else "float" if isinstance(value, float) else "integer"
            
            SystemConfig.set_value(
                db=db,
                key=field,
                value=value,
                value_type=value_type,
                description=f"Spiral learning configuration: {field.replace('_', ' ').title()}",
                category="spiral_learning"
            )
            updates[field] = value
    
    return await get_spiral_config(db, current_user)


@router.post("/config/spiral/reset")
async def reset_spiral_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Reset spiral learning configuration to default values (admin only)"""
    # Use the spiral learning config from DEFAULT_LEARNING_CONFIG
    spiral_keys = [
        "spiral_learning_enabled", "spiral_review_trigger_interval", "spiral_review_max_cards",
        "spiral_weakness_threshold", "spiral_stability_threshold", "spiral_integration_failure_weight"
    ]
    
    for key in spiral_keys:
        if key in DEFAULT_LEARNING_CONFIG:
            config = DEFAULT_LEARNING_CONFIG[key]
            SystemConfig.set_value(
                db=db,
                key=key,
                value=config["value"],
                value_type=config["type"],
                description=config["description"],
                category=config["category"]
            )
    
    return await get_spiral_config(db, current_user)
