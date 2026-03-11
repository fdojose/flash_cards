"""
Session Routes

FastAPI routes for managing learning sessions and flashcard interactions.
"""
from datetime import datetime, timedelta, timezone, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import random

from .models import UserLearningSet, UserLearningSetItem, UserElementReview, UserFieldAttempt
from .schemas import (
    SessionStartRequest, SessionResponse, FlashcardResponse, 
    AnswerSubmissionRequest, AnswerSubmissionResponse, ProgressResponse
)
from .fsrs_schemas import (
    FSRSIntegrationStats, StabilityStats, IntegrationCardDetail,
    IntegrationPerformanceMetrics
)
from ..auth.routes import get_current_user
from ..auth.models import User
from ..datasets.models import Dataset, Element, Field
from ..database import get_db
from ..admin.models import SystemConfig
from ..spaced.algorithms import FSRSAlgorithm, compute_fsrs_rating
from ..spaced.models import SpacedRepetitionConfig

# Import the progress update function
from ..dashboard.routes import _update_dataset_progress

# Gamification helpers (imported here to avoid circular-import issues at module level)
from ..gamification.models import UserStreak
from ..gamification.routes import check_mastery_badges, _check_streak_badges, _update_score
from ..dashboard.ranking_service import RankingService

router = APIRouter(prefix="/sessions", tags=["learning-sessions"])

# Configuration defaults
DEFAULT_INITIAL_SET_SIZE = 10
DEFAULT_STAGE_INCREMENT = 10
DEFAULT_MAX_SET_SIZE = 30
DEFAULT_MID_TIER_THRESHOLD = 80
DEFAULT_DISTRACTOR_COUNT = 3
DEFAULT_BATCH_SIZE = 5
DEFAULT_ISOLATION_MASTERY_PERCENTAGE = 0.8
DEFAULT_INTEGRATION_MASTERY_PERCENTAGE = 0.7
DEFAULT_MASTERY_REVIEW_WINDOW = 10

# Temporary in-memory storage for timer settings (until we add DB fields)
# In production, this would be stored in Redis or the database
timer_settings_cache = {}


def get_learning_config(db: Session):
    """Get current learning configuration from database or defaults"""
    return {
        'initial_set_size': SystemConfig.get_value(db, "initial_set_size", DEFAULT_INITIAL_SET_SIZE),
        'stage_increment': SystemConfig.get_value(db, "stage_increment", DEFAULT_STAGE_INCREMENT),
        'max_set_size': SystemConfig.get_value(db, "max_set_size", DEFAULT_MAX_SET_SIZE),
        'mid_tier_threshold': SystemConfig.get_value(db, "mid_tier_threshold", DEFAULT_MID_TIER_THRESHOLD),
        'chunk_size_progression': SystemConfig.get_value(db, "chunk_size_progression", "100,75,60,50"),
        'reinforcement_percentage': SystemConfig.get_value(db, "reinforcement_percentage", 10),
        'distractor_count': SystemConfig.get_value(db, "distractor_count", DEFAULT_DISTRACTOR_COUNT),
        'batch_size': SystemConfig.get_value(db, "batch_size", DEFAULT_BATCH_SIZE),
        'isolation_mastery_percentage': SystemConfig.get_value(db, "isolation_mastery_percentage", DEFAULT_ISOLATION_MASTERY_PERCENTAGE),
        'integration_mastery_percentage': SystemConfig.get_value(db, "integration_mastery_percentage", DEFAULT_INTEGRATION_MASTERY_PERCENTAGE),
        'mastery_review_window': SystemConfig.get_value(db, "mastery_review_window", DEFAULT_MASTERY_REVIEW_WINDOW),
    }


def get_fsrs_config(db: Session, user_id) -> dict:
    """Load FSRS parameters from SpacedRepetitionConfig, falling back to defaults."""
    cfg = db.query(SpacedRepetitionConfig).filter(
        SpacedRepetitionConfig.user_id == user_id
    ).first()
    return {
        'desired_retention': cfg.desired_retention if cfg else 0.9,
        'maximum_interval': cfg.maximum_interval if cfg else 365,
        'fast_threshold_ms': 3000,
        'slow_threshold_ms': 8000,
    }


def get_classification_config(db: Session) -> dict:
    """Get comprehensive configurable classification criteria for all learning phases"""
    config_keys = [
        # Learning phase criteria
        'learning_min_attempts',
        'learning_accuracy_threshold',
        'learning_success_streak_required',
        
        # Isolation mastery criteria
        'isolation_mastery_attempts_required',
        'isolation_mastery_accuracy_threshold', 
        'isolation_mastery_success_streak_required',
        'isolation_mastery_window_days',
        
        # Integration review criteria
        'integration_confirmation_attempts_required',
        'integration_confirmation_accuracy_threshold',
        'integration_max_failure_attempts',
        'integration_review_penalty_factor',
        
        # Integration confirmed criteria
        'integration_confirmed_maintenance_threshold',
        'integration_confirmed_stability_boost',
        'integration_confirmed_failure_penalty',
        
        # Spiral review criteria
        'spiral_review_trigger_cycles',
        'spiral_review_weakness_threshold',
        'spiral_review_stability_threshold',
        'spiral_review_max_cards',
        'spiral_review_success_threshold',
        
        # Status transition rules
        'allow_status_downgrading',
        'remediation_attempts_threshold',
        'consolidation_window_hours',
        
        # Attempt tracking configuration
        'track_isolation_attempts',
        'track_integration_attempts', 
        'track_spiral_attempts',
        'reset_attempts_on_mastery'
    ]
    
    defaults = {
        # Learning phase - more lenient for initial learning
        'learning_min_attempts': 2,
        'learning_accuracy_threshold': 0.6,
        'learning_success_streak_required': 0,
        
        # Isolation mastery - standard mastery requirements
        'isolation_mastery_attempts_required': 3,
        'isolation_mastery_accuracy_threshold': 0.8,
        'isolation_mastery_success_streak_required': 2,
        'isolation_mastery_window_days': 1,
        
        # Integration confirmation - confirmation focus
        'integration_confirmation_attempts_required': 1,
        'integration_confirmation_accuracy_threshold': 1.0,
        'integration_max_failure_attempts': 3,
        'integration_review_penalty_factor': 0.8,
        
        # Integration confirmed - maintenance focus
        'integration_confirmed_maintenance_threshold': 0.9,
        'integration_confirmed_stability_boost': 1.1,
        'integration_confirmed_failure_penalty': 0.95,
        
        # Spiral review - weakness remediation
        'spiral_review_trigger_cycles': 2,
        'spiral_review_weakness_threshold': 0.7,
        'spiral_review_stability_threshold': 1.5,
        'spiral_review_max_cards': 20,
        'spiral_review_success_threshold': 0.8,
        
        # Status transition rules - forward progression only
        'allow_status_downgrading': False,
        'remediation_attempts_threshold': 5,
        'consolidation_window_hours': 24,
        
        # Attempt tracking - comprehensive tracking enabled
        'track_isolation_attempts': True,
        'track_integration_attempts': True,
        'track_spiral_attempts': True,
        'reset_attempts_on_mastery': False
    }
    
    # Build config dict using SystemConfig.get_value method
    config_dict = {}
    for key in config_keys:
        config_dict[key] = SystemConfig.get_value(db, key, defaults[key])
    
    return config_dict


def get_integration_config(db: Session) -> dict:
    """Fetch admin-configured FSRS integration parameters"""
    config_keys = [
        'integration_enhancement_enabled',
        'integration_confirmation_threshold',
        'integration_max_attempts',
        'stability_boost_factor',
        'stability_decay_factor',
        'stability_max_score',
        'integration_failure_penalty',
        'reconsolidation_threshold',
        'stability_maintenance_boost',
        # Mastery window configuration parameters
        'default_mastery_window',
        'isolation_min_mastery_window',
        'isolation_max_mastery_window', 
        'isolation_field_multiplier',
        'single_field_mastery_window',
        'two_field_mastery_window',
        'integration_mastery_window',
        'required_mastery_window',
        'isolation_mastery_percentage',
        'initial_stability_score'
    ]
    
    # Defaults for all parameters
    defaults = {
        'integration_enhancement_enabled': False,
        'integration_confirmation_threshold': 1.0,
        'integration_max_attempts': 3,
        'stability_boost_factor': 1.2,
        'stability_decay_factor': 0.8,
        'stability_max_score': 3.0,
        'integration_failure_penalty': 0.9,
        'reconsolidation_threshold': 2,
        'stability_maintenance_boost': 1.05,
        # Mastery window defaults
        'default_mastery_window': 3,
        'isolation_min_mastery_window': 2,
        'isolation_max_mastery_window': 8,
        'isolation_field_multiplier': 1.5,
        'single_field_mastery_window': 2,
        'two_field_mastery_window': 3,
        'integration_mastery_window': 1,
        'required_mastery_window': 3,
        'isolation_mastery_percentage': 0.8,
        'initial_stability_score': 1.0
    }
    
    # Build config dict using SystemConfig.get_value method
    config_dict = {}
    for key in config_keys:
        config_dict[key] = SystemConfig.get_value(db, key, defaults[key])
            
    return config_dict


def get_dynamic_mastery_window(db: Session, dataset_id: str, learning_set: UserLearningSet, config: dict, field_count_override: int = None):
    """Calculate research-based dynamic mastery window with FSRS integration awareness"""
    
    # Use override for testing, otherwise get field count from database
    if field_count_override is not None:
        field_count = field_count_override
    else:
        # Get field count (existing logic)
        sample_element = db.query(Element).filter(Element.dataset_id == dataset_id).first()
        if not sample_element:
            return config.get('default_mastery_window', 3)
        
        fields = db.query(Field).filter(Field.element_id == sample_element.id).all()
        field_count = len(list(set([f.field_name for f in fields])))
    
    # Phase-aware calculation with admin-configurable parameters
    if learning_set.isolation_phase:
        # Isolation phase: Research-optimized logic with admin configuration
        min_window = config.get('isolation_min_mastery_window', 2)
        max_window = config.get('isolation_max_mastery_window', 8)
        field_multiplier = config.get('isolation_field_multiplier', 1.5)
        
        if field_count == 1:
            # Single field cards: Minimum attempts for reliability  
            return max(min_window, config.get('single_field_mastery_window', 2))
        elif field_count == 2:
            # Q&A pairs: window of 5 lets 80% threshold allow one error (4/5)
            return config.get('two_field_mastery_window', 5)
        elif field_count <= 4:
            # Small field count: Add one attempt per field
            return min(field_count + 1, max_window)
        else:
            # Large field count: Use configurable multiplier
            return min(int(field_count * field_multiplier), max_window)
    else:
        # Integration phase: FSRS-inspired logic
        return config.get('integration_mastery_window', 1)  # Single confirmation attempt for integration


def calculate_integration_mastery(db: Session, review: UserElementReview, recent_attempts: List[UserFieldAttempt], learning_set: UserLearningSet, config: dict):
    """FSRS-inspired integration mastery calculation with admin-configurable parameters"""
    
    # Input validation
    if not review or not learning_set or not config:
        return False
    
    if learning_set.isolation_phase:
        # Isolation phase: Use existing logic
        return calculate_isolation_mastery(review, recent_attempts, config)
    
    # Check if FSRS integration enhancement is enabled
    if not config.get('integration_enhancement_enabled', False):
        # Enhancement disabled: use simple, phase-aware logic
        if learning_set.isolation_phase:
            return calculate_isolation_mastery(review, recent_attempts, config)
        # Integration: confirm on simple rule (default window=1)
        integration_window = config.get('integration_mastery_window', 1)
        threshold = config.get('integration_confirmation_threshold', 1.0)
        if len(recent_attempts) >= 1:
            if integration_window == 1:
                if recent_attempts[0].is_correct:
                    review.integration_confirmed = True
                    return True
                else:
                    review.status = "integration_review"
                    review.integration_attempts = (review.integration_attempts or 0) + 1
                    return False
            else:
                total = len(recent_attempts)
                correct = sum(1 for a in recent_attempts if a.is_correct)
                accuracy = correct / total if total > 0 else 0.0
                if accuracy >= threshold:
                    review.integration_confirmed = True
                    return True
                else:
                    review.status = "integration_review"
                    review.integration_attempts = (review.integration_attempts or 0) + 1
                    return False
        return False
    
    # Integration phase: FSRS-inspired logic with admin configuration
    integration_threshold = config.get('integration_confirmation_threshold', 1.0)
    max_attempts = config.get('integration_max_attempts', 3)
    boost_factor = config.get('stability_boost_factor', 1.2)
    decay_factor = config.get('stability_decay_factor', 0.8)
    max_stability = config.get('stability_max_score', 3.0)
    failure_penalty = config.get('integration_failure_penalty', 0.9)
    reconsolidation_threshold = config.get('reconsolidation_threshold', 2)
    
    # Initialize stability_score if not set
    if not hasattr(review, 'stability_score') or review.stability_score is None:
        review.stability_score = config.get('initial_stability_score', 1.0)
    
    if review.status == "mastered" and not review.integration_confirmed:
        # Card was mastered in isolation, needs integration confirmation
        if len(recent_attempts) >= 1:
            # For integration confirmation with integration_mastery_window=1, 
            # check if the most recent attempt is correct (simple confirmation)
            integration_window = config.get('integration_mastery_window', 1)
            
            if integration_window == 1:
                # Single attempt confirmation - check if the recent attempt is correct
                if recent_attempts[0].is_correct:
                    # Successful integration confirmation - no need to increment attempts on success
                    review.integration_confirmed = True
                    review.stability_score = min(review.stability_score * boost_factor, max_stability)
                    review.status = "mastered"
                    return True
                else:
                    # Failed integration confirmation - increment attempts and move to review
                    review.status = "integration_review"
                    review.integration_attempts += 1
                    review.stability_score *= decay_factor
                    return False
            else:
                # Multiple attempts evaluation - use accuracy threshold
                total_attempts = len(recent_attempts)
                correct_attempts = sum(1 for attempt in recent_attempts if attempt.is_correct)
                accuracy = correct_attempts / total_attempts if total_attempts > 0 else 0.0
                
                if accuracy >= integration_threshold:
                    # Successful integration confirmation - no need to increment attempts on success
                    review.integration_confirmed = True
                    review.stability_score = min(review.stability_score * boost_factor, max_stability)
                    review.status = "mastered"
                    return True
                else:
                    # Failed integration confirmation - increment attempts and move to review
                    review.status = "integration_review"
                    review.integration_attempts += 1
                    review.stability_score *= decay_factor
                    return False
            
    elif review.status == "integration_review":
        # Card failed integration, needs re-confirmation (NOT full re-learning)
        if len(recent_attempts) >= 1:
            # For integration re-confirmation, use same logic as initial confirmation
            integration_window = config.get('integration_mastery_window', 1)
            
            if integration_window == 1:
                # Single attempt re-confirmation - check if the recent attempt is correct
                if recent_attempts[0].is_correct:
                    # Successful re-confirmation
                    review.integration_confirmed = True
                    review.status = "mastered"
                    review.stability_score = min(review.stability_score * boost_factor, max_stability)
                    return True
                else:
                    # Failed re-confirmation - increment attempts and check max
                    review.integration_attempts += 1
                    review.stability_score *= decay_factor
                    
                    if review.integration_attempts >= max_attempts:
                        # Multiple integration failures - return to isolation learning
                        review.status = "learning"
                        review.integration_confirmed = False
                        review.stability_score = 0.5  # Reset stability for re-isolation
                    return False
            else:
                # Multiple attempts evaluation - use accuracy threshold
                total_attempts = len(recent_attempts)
                correct_attempts = sum(1 for attempt in recent_attempts if attempt.is_correct)
                accuracy = correct_attempts / total_attempts if total_attempts > 0 else 0.0
                
                if accuracy >= integration_threshold:
                    # Successful re-confirmation
                    review.integration_confirmed = True
                    review.status = "mastered"
                    review.stability_score = min(review.stability_score * boost_factor, max_stability)
                    return True
                else:
                    # Failed re-confirmation - increment attempts and check max
                    review.integration_attempts += 1
                    review.stability_score *= decay_factor
                    
                    if review.integration_attempts >= max_attempts:
                        # Multiple integration failures - return to isolation learning
                        review.status = "learning"
                        review.integration_confirmed = False
                        review.stability_score = 0.5  # Reset stability for re-isolation
                    return False
                
    elif review.status == "learning":
        # Card still in learning phase - use isolation logic
        return calculate_isolation_mastery(review, recent_attempts, config)
        
    elif review.status == "mastered" and review.integration_confirmed:
        # Card already integration-confirmed, just maintain with admin-configurable penalty
        if len(recent_attempts) >= 1:
            if recent_attempts[-1].is_correct:
                # Use configurable maintenance boost instead of hardcoded 1.05
                maintenance_boost = config.get('stability_maintenance_boost', 1.05)
                review.stability_score = min(review.stability_score * maintenance_boost, max_stability)
            else:
                # Previously confirmed card failed - apply configurable penalty
                review.stability_score *= failure_penalty
                # Note: reconsolidation_threshold applies to integration_attempts, not confirmed card failures
                # This is maintenance failure, not integration failure
        return review.status == "mastered"
    
    return False


def calculate_isolation_mastery(review: UserElementReview, recent_attempts: List[UserFieldAttempt], config: dict):
    """Original isolation phase mastery logic with configurable parameters"""
    # Use configurable mastery window instead of hardcoded length
    required_window = config.get('required_mastery_window', 3)  # Default 3 for backwards compatibility
    
    if len(recent_attempts) >= required_window:
        correct_attempts = sum(1 for attempt in recent_attempts if attempt.is_correct)
        accuracy_percentage = correct_attempts / len(recent_attempts)
        mastery_threshold = config.get('isolation_mastery_percentage', 0.8)
        
        if accuracy_percentage >= mastery_threshold:
            review.status = "mastered"
            review.accuracy_percentage = accuracy_percentage
            # Use admin-configured initial stability for newly mastered cards
            review.stability_score = config.get('initial_stability_score', 1.0)
            return True
    
    return False


def classify_card_status(db: Session, review: UserElementReview, recent_attempts: List[UserFieldAttempt], learning_set: UserLearningSet) -> str:
    """
    Comprehensive configurable card classification system.
    Determines the appropriate status for a card based on admin-configurable criteria.
    
    Returns the new status for the card.
    """
    if not review or not recent_attempts:
        return "learning"
    
    # Get classification configuration
    config = get_classification_config(db)
    
    current_status = review.status or "learning"
    # Treat "new" status as "learning" for classification purposes
    if current_status == "new":
        current_status = "learning"
        
    total_attempts = len(recent_attempts)
    correct_attempts = sum(1 for attempt in recent_attempts if attempt.is_correct)
    accuracy = correct_attempts / total_attempts if total_attempts > 0 else 0.0
    
    # Status can only progress forward unless downgrading is explicitly enabled
    allow_downgrading = config.get('allow_status_downgrading', False)
    
    # Learning phase classification (includes "new" cards)
    if current_status == "learning":
        return classify_learning_status(review, recent_attempts, config, learning_set)
    
    # Isolation mastered classification  
    elif current_status == "isolation_mastered":
        return classify_isolation_mastered_status(review, recent_attempts, config, learning_set)
    
    # Integration review classification
    elif current_status == "integration_review":
        return classify_integration_review_status(review, recent_attempts, config)
        
    # Integration confirmed classification
    elif current_status == "integration_confirmed":
        return classify_integration_confirmed_status(review, recent_attempts, config, allow_downgrading)
        
    # Spiral review classification
    elif current_status == "spiral_review":
        return classify_spiral_review_status(review, recent_attempts, config)
    
    # Fallback to current status
    return current_status


def classify_learning_status(review: UserElementReview, recent_attempts: List[UserFieldAttempt], config: dict, learning_set: UserLearningSet) -> str:
    """Classify cards in learning phase using configurable criteria"""
    min_attempts = config.get('learning_min_attempts', 2)
    accuracy_threshold = config.get('learning_accuracy_threshold', 0.6)
    success_streak_required = config.get('learning_success_streak_required', 0)
    
    # Check if we have enough attempts
    if len(recent_attempts) < min_attempts:
        return "learning"
    
    # Calculate metrics
    total_attempts = len(recent_attempts)
    correct_attempts = sum(1 for attempt in recent_attempts if attempt.is_correct)
    accuracy = correct_attempts / total_attempts if total_attempts > 0 else 0.0
    
    # Calculate success streak from most recent to oldest
    # recent_attempts is ordered DESC (newest first), so iterate directly (no reversed)
    success_streak = 0
    for attempt in recent_attempts:
        if attempt.is_correct:
            success_streak += 1
        else:
            break

    # Check for isolation mastery progression
    isolation_attempts_required = config.get('isolation_mastery_attempts_required', 3)
    isolation_accuracy_threshold = config.get('isolation_mastery_accuracy_threshold', 0.8)
    isolation_success_streak_required = config.get('isolation_mastery_success_streak_required', 2)
    
    if (total_attempts >= isolation_attempts_required and 
        accuracy >= isolation_accuracy_threshold and
        success_streak >= isolation_success_streak_required):
        
        # Update review fields for isolation mastery
        review.accuracy_percentage = accuracy
        review.integration_attempts = (review.integration_attempts or 0) + 1
        review.stability_score = config.get('initial_stability_score', 1.0)
        
        # Track isolation attempts if enabled
        if config.get('track_isolation_attempts', True):
            review.success_streak = correct_attempts
        
        return "isolation_mastered"
    
    # Check for basic learning progression (but not mastery)
    elif accuracy >= accuracy_threshold and success_streak >= success_streak_required:
        return "learning"  # Still learning but progressing well
    
    return "learning"


def classify_isolation_mastered_status(review: UserElementReview, recent_attempts: List[UserFieldAttempt], config: dict, learning_set: UserLearningSet) -> str:
    """Classify isolation mastered cards for integration phase transition"""
    
    # Check if we're in integration phase
    if not learning_set.isolation_phase:
        # Card is isolation mastered and we're in integration phase
        
        # If the card has not had any integration attempts yet, transition to integration_review
        # to require integration confirmation attempts
        if not hasattr(review, 'last_integration_attempt') or review.last_integration_attempt is None:
            # First time encountering this isolation_mastered card in integration phase
            # Transition to integration_review to require confirmation
            return "integration_review"
        
        # If the card has been attempted in integration phase, check confirmation status
        confirmation_attempts_required = config.get('integration_confirmation_attempts_required', 1)
        confirmation_accuracy_threshold = config.get('integration_confirmation_accuracy_threshold', 1.0)
        
        # Only consider attempts made during integration phase (after last_integration_attempt timestamp)
        integration_attempts = []
        if review.last_integration_attempt:
            integration_attempts = []
            for attempt in recent_attempts:
                # Fix timezone comparison issue
                attempt_time = attempt.attempted_at
                start_time = review.last_integration_attempt
                
                # Make both datetimes compatible for comparison
                if attempt_time.tzinfo is None and start_time.tzinfo is not None:
                    attempt_time = attempt_time.replace(tzinfo=timezone.utc)
                elif attempt_time.tzinfo is not None and start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)
                
                if attempt_time >= start_time:
                    integration_attempts.append(attempt)
        
        if len(integration_attempts) >= confirmation_attempts_required:
            total_attempts = len(integration_attempts)
            correct_attempts = sum(1 for attempt in integration_attempts if attempt.is_correct)
            accuracy = correct_attempts / total_attempts if total_attempts > 0 else 0.0
            
            if accuracy >= confirmation_accuracy_threshold:
                # Successful integration confirmation
                review.integration_confirmed = True
                # Note: Do NOT increment integration_attempts on success - only on failures
                
                # Apply stability boost
                stability_boost = config.get('integration_confirmed_stability_boost', 1.1)
                review.stability_score = min(
                    (review.stability_score or 1.0) * stability_boost,
                    config.get('stability_max_score', 3.0)
                )
                
                # Track integration attempts if enabled
                if config.get('track_integration_attempts', True):
                    review.integration_success_count = correct_attempts
                
                return "integration_confirmed"
            else:
                # Failed integration confirmation
                review.integration_attempts = (review.integration_attempts or 0) + 1
                
                # Check if max failures reached
                max_failures = config.get('integration_max_failure_attempts', 3)
                if review.integration_attempts >= max_failures:
                    # Reset to learning with penalty
                    review.stability_score = (review.stability_score or 1.0) * config.get('integration_review_penalty_factor', 0.8)
                    review.integration_confirmed = False
                    return "learning"  # Back to learning after multiple integration failures
                
                return "integration_review"
        else:
            # Not enough integration attempts yet, stay in integration_review
            return "integration_review"
    
    # Still in isolation phase or no recent attempts
    return "isolation_mastered"


def classify_integration_review_status(review: UserElementReview, recent_attempts: List[UserFieldAttempt], config: dict) -> str:
    """Classify cards in integration review (failed initial integration)"""
    confirmation_attempts_required = config.get('integration_confirmation_attempts_required', 1)
    confirmation_accuracy_threshold = config.get('integration_confirmation_accuracy_threshold', 1.0)
    max_failures = config.get('integration_max_failure_attempts', 3)
    
    if len(recent_attempts) >= confirmation_attempts_required:
        total_attempts = len(recent_attempts)
        correct_attempts = sum(1 for attempt in recent_attempts if attempt.is_correct)
        accuracy = correct_attempts / total_attempts if total_attempts > 0 else 0.0
        
        if accuracy >= confirmation_accuracy_threshold:
            # Successful integration recovery
            review.integration_confirmed = True
            
            # Apply recovery boost (smaller than initial confirmation)
            stability_boost = config.get('integration_confirmed_stability_boost', 1.1) * 0.9  # Reduced boost for recovery
            review.stability_score = min(
                (review.stability_score or 1.0) * stability_boost,
                config.get('stability_max_score', 3.0)
            )
            
            return "integration_confirmed"
        else:
            # Still failing integration
            review.integration_attempts = (review.integration_attempts or 0) + 1
            
            if review.integration_attempts >= max_failures:
                # Multiple failures - return to learning
                review.stability_score = (review.stability_score or 1.0) * config.get('integration_review_penalty_factor', 0.8)
                review.integration_confirmed = False
                return "learning"
    
    return "integration_review"


def classify_integration_confirmed_status(review: UserElementReview, recent_attempts: List[UserFieldAttempt], config: dict, allow_downgrading: bool) -> str:
    """Classify integration confirmed cards (maintenance phase)"""
    maintenance_threshold = config.get('integration_confirmed_maintenance_threshold', 0.9)
    failure_penalty = config.get('integration_confirmed_failure_penalty', 0.95)
    stability_boost = config.get('integration_confirmed_stability_boost', 1.1)
    
    if len(recent_attempts) >= 1:
        # Check most recent performance
        recent_correct = sum(1 for attempt in recent_attempts[-3:] if attempt.is_correct)  # Last 3 attempts
        recent_total = min(len(recent_attempts), 3)
        recent_accuracy = recent_correct / recent_total if recent_total > 0 else 0.0
        
        if recent_accuracy >= maintenance_threshold:
            # Good maintenance performance - apply boost
            review.stability_score = min(
                (review.stability_score or 1.0) * stability_boost,
                config.get('stability_max_score', 3.0)
            )
            return "integration_confirmed"
        elif recent_accuracy < 0.5 and allow_downgrading:
            # Poor performance and downgrading allowed
            review.stability_score = (review.stability_score or 1.0) * failure_penalty
            
            # Check if stability is too low for confirmed status
            if review.stability_score < 1.0:
                return "integration_review"
        else:
            # Apply penalty but maintain status
            review.stability_score = (review.stability_score or 1.0) * failure_penalty
    
    return "integration_confirmed"


def classify_spiral_review_status(review: UserElementReview, recent_attempts: List[UserFieldAttempt], config: dict) -> str:
    """Classify cards in spiral review (weakness remediation)"""
    success_threshold = config.get('spiral_review_success_threshold', 0.8)
    min_attempts = config.get('learning_min_attempts', 2)  # Reuse learning min attempts
    
    if len(recent_attempts) >= min_attempts:
        total_attempts = len(recent_attempts)
        correct_attempts = sum(1 for attempt in recent_attempts if attempt.is_correct)
        accuracy = correct_attempts / total_attempts if total_attempts > 0 else 0.0
        
        if accuracy >= success_threshold:
            # Spiral review successful - return to previous confirmed status
            review.spiral_attempts = (review.spiral_attempts or 0) + 1
            
            # Track spiral attempts if enabled
            if config.get('track_spiral_attempts', True):
                review.spiral_success_count = correct_attempts
            
            # Apply stability recovery boost
            stability_boost = config.get('integration_confirmed_stability_boost', 1.1)
            review.stability_score = min(
                (review.stability_score or 1.0) * stability_boost,
                config.get('stability_max_score', 3.0)
            )
            
            return "integration_confirmed"  # Return to integration confirmed after successful spiral review
    
    # Continue spiral review
    return "spiral_review"


def should_trigger_spiral_review(db: Session, user_id: str, dataset_id: str, learning_set: UserLearningSet, config: dict) -> tuple[bool, List]:
    """Check if spiral review should be triggered based on configurable criteria"""
    spiral_enabled = config.get('spiral_review_trigger_cycles', 2) > 0
    trigger_cycles = config.get('spiral_review_trigger_cycles', 2)
    
    if not spiral_enabled:
        return False, []
    
    cycles_completed = learning_set.completed_integration_cycles or 0
    
    # Trigger spiral review every N integration cycles
    if cycles_completed > 0 and cycles_completed % trigger_cycles == 0:
        # Get weak cards for spiral review
        weak_cards = identify_weak_cards_for_spiral_review(db, user_id, dataset_id, learning_set.current_batch_end, config)
        return len(weak_cards) > 0, weak_cards
    
    return False, []


def identify_weak_cards_for_spiral_review(db: Session, user_id: str, dataset_id: str, end_position: int, config: dict) -> List:
    """Identify weak cards that need spiral review using configurable criteria"""
    weakness_threshold = config.get('spiral_review_weakness_threshold', 0.7)
    stability_threshold = config.get('spiral_review_stability_threshold', 1.5)
    max_cards = config.get('spiral_review_max_cards', 20)
    
    # Query cards that meet weakness criteria
    weak_reviews = db.query(UserElementReview).join(
        Element, UserElementReview.element_id == Element.id
    ).join(
        UserLearningSetItem, Element.id == UserLearningSetItem.element_id
    ).join(
        UserLearningSet, UserLearningSetItem.learning_set_id == UserLearningSet.id
    ).filter(
        and_(
            UserElementReview.user_id == user_id,
            Element.dataset_id == dataset_id,
            UserLearningSet.dataset_id == dataset_id,
            UserLearningSetItem.position <= end_position,
            or_(
                UserElementReview.accuracy_percentage < weakness_threshold,
                UserElementReview.stability_score < stability_threshold,
                UserElementReview.integration_attempts > 2
            )
        )
    ).limit(max_cards).all()
    
    return [review.element_id for review in weak_reviews]


def update_card_classification(db: Session, review: UserElementReview, recent_attempts: List[UserFieldAttempt], learning_set: UserLearningSet):
    """Update a card's classification based on recent performance"""
    new_status = classify_card_status(db, review, recent_attempts, learning_set)
    old_status = review.status
    
    if new_status != old_status:
        print(f"DEBUG: Card {review.element_id} status change: {old_status} -> {new_status}")
        review.status = new_status
        
        # Update timestamps for status transitions
        review.last_status_change = datetime.now(timezone.utc)
        
        # Reset attempts on mastery if configured
        config = get_classification_config(db)
        if config.get('reset_attempts_on_mastery', False) and new_status in ["isolation_mastered", "integration_confirmed"]:
            # Reset appropriate attempt counters
            if new_status == "isolation_mastered":
                review.integration_attempts = 0
            elif new_status == "integration_confirmed":
                review.integration_attempts = 0


def get_optimal_learning_parameters(total_elements: int, base_config: dict):
    """
    Calculate optimal learning parameters based on dataset size using tiered logic.
    
    Tiered Logic:
    - ≤15 cards: Show all at once (no progression needed)
    - 16-mid_tier_threshold cards: Start with configured size, increment by configured amount (faster progression)  
    - (mid_tier_threshold+1)-max_set_size cards: Start with 15, increment by 15 (traditional)
    - >max_set_size cards: Use chunked learning
    """
    if total_elements <= base_config['initial_set_size']:
        return {
            'initial_set_size': total_elements,
            'stage_increment': 0,  # No progression needed
            'message': f"Perfect! All {total_elements} cards will be available immediately.",
            'is_chunked': False,
            'is_optimized': True
        }
    elif total_elements <= base_config['mid_tier_threshold']:
        return {
            'initial_set_size': base_config['initial_set_size'],
            'stage_increment': base_config['stage_increment'],
            'message': f"You're starting with {base_config['initial_set_size']} cards today — you'll unlock the remaining {total_elements - base_config['initial_set_size']} after mastering these! 🎯",
            'is_chunked': False,
            'is_optimized': True
        }
    elif total_elements <= base_config['max_set_size']:  # 81-100
        return {
            'initial_set_size': base_config['initial_set_size'],  # 15
            'stage_increment': base_config['stage_increment'],    # 15
            'message': f"Starting with {base_config['initial_set_size']} cards, gradually expanding to all {total_elements} cards.",
            'is_chunked': False,
            'is_optimized': False
        }
    else:  # >100 cards - chunked learning
        chunk_size = get_adaptive_chunk_size(1, base_config['chunk_size_progression'])
        total_chunks = calculate_total_chunks(total_elements, base_config['chunk_size_progression'])
        return {
            'initial_set_size': chunk_size,
            'stage_increment': 0,  # No increment in chunked mode
            'message': f"🧪 Large dataset detected! Starting Chunk 1 of {total_chunks} with {chunk_size} cards. Adaptive sizing will help prevent burnout!",
            'is_chunked': True,
            'is_optimized': True
        }


def get_stage_increment_for_learning_set(learning_set, base_config: dict):
    """Get the appropriate stage increment for a learning set based on its dataset size"""
    if learning_set.total_dataset_size:
        optimal_params = get_optimal_learning_parameters(learning_set.total_dataset_size, base_config)
        return optimal_params['stage_increment']
    else:
        # Fallback to base config if dataset size is not stored
        return base_config['stage_increment']


def get_adaptive_chunk_size(chunk_number: int, chunk_progression: str) -> int:
    """Get adaptive chunk size based on chunk number and progression"""
    try:
        sizes = [int(x.strip()) for x in chunk_progression.split(',')]
        if chunk_number <= len(sizes):
            return sizes[chunk_number - 1]
        else:
            # Use the last size for subsequent chunks
            return sizes[-1]
    except (ValueError, IndexError):
        # Fallback to default if configuration is invalid
        return 100


def calculate_total_chunks(total_elements: int, chunk_progression: str) -> int:
    """Calculate total number of chunks needed for the dataset"""
    try:
        sizes = [int(x.strip()) for x in chunk_progression.split(',')]
        remaining = total_elements
        chunks = 0
        
        for size in sizes:
            if remaining <= 0:
                break
            chunks += 1
            remaining -= size
        
        # If there are still remaining elements, continue with the last chunk size
        if remaining > 0:
            last_size = sizes[-1]
            additional_chunks = (remaining + last_size - 1) // last_size  # Ceiling division
            chunks += additional_chunks
        
        return chunks
    except (ValueError, IndexError):
        # Fallback calculation
        return (total_elements + 99) // 100  # Ceiling division by 100


def get_reinforcement_items(db: Session, learning_set, reinforcement_percentage: int):
    """Get random items from previous chunks for reinforcement"""
    if learning_set.chunk_number <= 1:
        return []
    
    # Get all previously mastered elements from this user and dataset
    # that are NOT in the current learning set
    current_element_ids = [item.element_id for item in learning_set.items]
    
    previous_mastered = db.query(UserElementReview).filter(
        and_(
            UserElementReview.user_id == learning_set.user_id,
            UserElementReview.status.in_(["isolation_mastered", "integration_confirmed"]),
            ~UserElementReview.element_id.in_(current_element_ids)
        )
    ).join(Element).filter(Element.dataset_id == learning_set.dataset_id).all()
    
    if not previous_mastered:
        return []
    
    # Calculate how many reinforcement items to include
    current_chunk_size = learning_set.chunk_size or 100
    reinforcement_count = max(1, (current_chunk_size * reinforcement_percentage) // 100)
    reinforcement_count = min(reinforcement_count, len(previous_mastered))
    
    # Randomly select reinforcement items
    import random
    selected_reviews = random.sample(previous_mastered, reinforcement_count)
    
    # Get the actual elements
    element_ids = [review.element_id for review in selected_reviews]
    return db.query(Element).filter(Element.id.in_(element_ids)).all()


# Spiral Learning Helper Functions

def should_trigger_spiral_review(db: Session, user_id: str, dataset_id: str, end_position: int, config: dict) -> tuple[bool, str]:
    """
    Check if spiral review should be triggered after integration completion.
    
    Returns:
        tuple: (should_trigger: bool, review_range: str)
    """
    # Get spiral learning configuration
    spiral_enabled = config.get('spiral_learning_enabled', True)
    trigger_interval = config.get('spiral_review_trigger_interval', 2)
    
    if not spiral_enabled:
        return False, ""
    
    # Get the current learning set to check integration cycle count
    learning_set = db.query(UserLearningSet).filter(
        and_(
            UserLearningSet.user_id == user_id,
            UserLearningSet.dataset_id == dataset_id,
            UserLearningSet.status == "active"
        )
    ).first()
    
    if not learning_set:
        return False, ""
    
    cycles_completed = learning_set.completed_integration_cycles or 0
    
    # Trigger spiral review every N integration cycles
    if cycles_completed > 0 and cycles_completed % trigger_interval == 0:
        review_range = f"positions 1-{end_position}"
        return True, review_range
    
    return False, ""


def get_spiral_review_cards(db: Session, user_id: str, dataset_id: str, end_position: int, config: dict) -> List:
    """
    Identify cards that need spiral review based on weakness indicators.
    
    Returns cards that are weak based on:
    - Low accuracy percentage
    - Low stability score  
    - Integration attempt failures
    - Recent performance issues
    """
    weakness_threshold = config.get('spiral_weakness_threshold', 0.6)
    stability_threshold = config.get('spiral_stability_threshold', 1.5)
    integration_failure_weight = config.get('spiral_integration_failure_weight', 2.0)
    max_cards = config.get('spiral_review_max_cards', 20)
    
    # Get all elements in the range that have been reviewed
    elements_with_reviews = db.query(
        Element,
        UserElementReview.accuracy_percentage,
        UserElementReview.stability_score,
        UserElementReview.integration_attempts,
        UserElementReview.review_count
    ).join(
        UserElementReview, Element.id == UserElementReview.element_id
    ).join(
        UserLearningSetItem, Element.id == UserLearningSetItem.element_id
    ).join(
        UserLearningSet, UserLearningSetItem.learning_set_id == UserLearningSet.id
    ).filter(
        and_(
            Element.dataset_id == dataset_id,
            UserElementReview.user_id == user_id,
            UserLearningSet.dataset_id == dataset_id,
            UserLearningSetItem.position <= end_position,
            UserElementReview.review_count > 0  # Only cards that have been reviewed
        )
    ).all()
    
    if not elements_with_reviews:
        return []
    
    # Calculate weakness scores for each card
    weakness_scores = []
    
    for element, accuracy, stability, integration_attempts, review_count in elements_with_reviews:
        # Calculate individual weakness components
        accuracy_score = max(0, weakness_threshold - (accuracy or 0.0))
        stability_score = max(0, stability_threshold - (stability or 1.0))
        integration_penalty = (integration_attempts or 0) * integration_failure_weight
        recency_bonus = 1.0 if (review_count or 0) < 3 else 0.5  # Newer cards get priority
        
        # Combined weakness score (higher = more weak)
        total_weakness = accuracy_score + stability_score + integration_penalty + recency_bonus
        
        # Only include cards that have some weakness
        if total_weakness > 0:
            weakness_scores.append((element, total_weakness))
    
    # Sort by weakness score (highest first) and limit to max_cards
    weakness_scores.sort(key=lambda x: x[1], reverse=True)
    return [element for element, score in weakness_scores[:max_cards]]


async def start_next_chunk(db: Session, current_learning_set, current_user):
    """Start the next chunk in chunked learning progression"""
    config = get_learning_config(db)
    
    # Calculate next chunk parameters
    next_chunk_number = current_learning_set.chunk_number + 1
    next_chunk_size = get_adaptive_chunk_size(next_chunk_number, config['chunk_size_progression'])
    
    # Mark current learning set as completed
    current_learning_set.status = "completed"
    
    # Create new learning set for next chunk
    new_learning_set = UserLearningSet(
        user_id=current_user.id,
        dataset_id=current_learning_set.dataset_id,
        stage=1,
        status="active",
        mode=current_learning_set.mode,
        chunk_number=next_chunk_number,
        total_chunks=current_learning_set.total_chunks,
        chunk_size=next_chunk_size,
        total_dataset_size=current_learning_set.total_dataset_size
    )
    db.add(new_learning_set)
    db.flush()
    
    # Get mastered element IDs to skip
    mastered_element_ids = db.query(UserElementReview.element_id).filter(
        and_(
            UserElementReview.user_id == current_user.id,
            UserElementReview.status.in_(["isolation_mastered", "integration_confirmed"])
        )
    ).join(Element).filter(Element.dataset_id == current_learning_set.dataset_id).subquery()
    
    # Get new elements for next chunk
    new_elements = db.query(Element).filter(
        and_(
            Element.dataset_id == current_learning_set.dataset_id,
            ~Element.id.in_(mastered_element_ids)
        )
    ).order_by(Element.created_at, Element.id).limit(next_chunk_size).all()
    
    # Get reinforcement elements
    reinforcement_elements = get_reinforcement_items(
        db, new_learning_set, config['reinforcement_percentage']
    )
    
    # Combine and shuffle elements
    elements = new_elements + reinforcement_elements
    import random
    random.shuffle(elements)
    
    # Add elements to new learning set
    for i, element in enumerate(elements):
        item = UserLearningSetItem(
            learning_set_id=new_learning_set.id,
            element_id=element.id,
            position=i + 1
        )
        db.add(item)
    
    db.commit()
    
    # Generate gamification message
    badge_earned = ""
    if next_chunk_number == 2:
        badge_earned = " 🥉 Progress Badge unlocked!"
    elif next_chunk_number == 3:
        badge_earned = " 🥈 Momentum Badge unlocked!"
    elif next_chunk_number >= 4:
        badge_earned = " 🥇 Champion Badge unlocked!"
    
    progress_message = f"🎉 Chunk {current_learning_set.chunk_number} of {current_learning_set.total_chunks} completed!{badge_earned} Starting Chunk {next_chunk_number} with {len(elements)} cards (including {len(reinforcement_elements)} reinforcement items). Keep going! 💪"
    
    return {
        "message": progress_message,
        "chunk_completed": current_learning_set.chunk_number,
        "chunk_started": next_chunk_number,
        "total_chunks": current_learning_set.total_chunks,
        "new_learning_set_id": new_learning_set.id,
        "badge_earned": badge_earned.strip(),
        "chunk_size": len(elements),
        "reinforcement_count": len(reinforcement_elements)
    }


@router.post("/start", response_model=SessionResponse)
async def start_session(
    request: SessionStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start or resume a learning session for a dataset"""
    # Initialize config to avoid UnboundLocalError
    config = get_learning_config(db)
    
    # Check if dataset exists
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Check for existing active learning set
    learning_set = db.query(UserLearningSet).filter(
        and_(
            UserLearningSet.user_id == current_user.id,
            UserLearningSet.dataset_id == request.dataset_id,
            UserLearningSet.status == "active"
        )
    ).first()
    
    # If force_review is requested, reset the learning progress
    if request.force_review and learning_set:
        # Reset all review statuses for this dataset to allow re-studying
        db.query(UserElementReview).filter(
            and_(
                UserElementReview.user_id == current_user.id,
                UserElementReview.element_id.in_(
                    db.query(Element.id).filter(Element.dataset_id == request.dataset_id)
                )
            )
        ).delete(synchronize_session=False)
        
        # Clear existing learning set items
        db.query(UserLearningSetItem).filter(
            UserLearningSetItem.learning_set_id == learning_set.id
        ).delete(synchronize_session=False)
        
        # Add ALL elements to the learning set for force review
        elements = db.query(Element).filter(Element.dataset_id == request.dataset_id).all()
        for i, element in enumerate(elements):
            item = UserLearningSetItem(
                learning_set_id=learning_set.id,
                element_id=element.id,
                position=i + 1
            )
            db.add(item)
        
        # Reset the learning set stage and set special mode for force review
        learning_set.stage = 1
        learning_set.mode = "force_review"  # Special mode for quick review
        db.commit()
        db.refresh(learning_set)
    
    if not learning_set:
        # Get current learning configuration
        config = get_learning_config(db)
        
        # Count total elements in dataset
        total_elements = db.query(Element).filter(Element.dataset_id == request.dataset_id).count()
        
        # Check for previously completed learning sets to determine continuation point
        last_completed_set = db.query(UserLearningSet).filter(
            and_(
                UserLearningSet.user_id == current_user.id,
                UserLearningSet.dataset_id == request.dataset_id,
                UserLearningSet.status == "completed"
            )
        ).order_by(UserLearningSet.created_at.desc()).first()
        
        # Determine starting batch position
        if last_completed_set and hasattr(last_completed_set, 'current_batch_end') and last_completed_set.current_batch_end:
            # Continue from where the last completed session ended
            next_batch_start = last_completed_set.current_batch_end + 1
            print(f"DEBUG: Continuing from previous session, starting at position {next_batch_start}")
        else:
            # Start from the beginning
            next_batch_start = 1
            print(f"DEBUG: Starting new session from position 1")
        
        # Get optimal learning parameters based on dataset size
        optimal_params = get_optimal_learning_parameters(total_elements, config)
        
        # Determine session parameters
        print(f"DEBUG: Session parameter decision - request.force_review={request.force_review}, optimal_params['is_chunked']={optimal_params['is_chunked']}")
        if request.force_review:
            # For force review, include ALL elements in one session
            print(f"DEBUG: Taking FORCE_REVIEW path")
            chunk_number = 1
            total_chunks = 1
            current_chunk_size = total_elements
            learning_message = f"Force review mode: All {total_elements} cards will be reviewed."
            # Reset to start from beginning for force review
            next_batch_start = 1
        elif optimal_params['is_chunked']:
            # Chunked learning for large datasets
            print(f"DEBUG: Taking CHUNKED_LEARNING path")
            chunk_number = 1
            total_chunks = calculate_total_chunks(total_elements, config['chunk_size_progression'])
            current_chunk_size = get_adaptive_chunk_size(chunk_number, config['chunk_size_progression'])
            learning_message = optimal_params['message']
            # Reset to start from beginning for chunked learning
            next_batch_start = 1
        else:
            # Regular or optimized progressive learning
            print(f"DEBUG: Taking REGULAR_PROGRESSIVE_LEARNING path")
            chunk_number = None
            total_chunks = None
            # For batch-based learning, use batch_size instead of optimal params
            current_chunk_size = config['batch_size']  # Force to batch_size for consistency
            
            # Check if we're at the end of the dataset
            if next_batch_start > total_elements:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT,
                    detail="🎉 Congratulations! You've already completed the entire dataset! All cards mastered! 🏆"
                )
            
            remaining_cards = min(config['batch_size'], total_elements - next_batch_start + 1)
            learning_message = f"Continuing with {remaining_cards} cards (positions {next_batch_start}-{next_batch_start + remaining_cards - 1}) — master these to unlock more! 🎯"
        
        # Create new learning set
        batch_size = config['batch_size']
        next_batch_end = min(next_batch_start + batch_size - 1, total_elements)
        
        learning_set = UserLearningSet(
            user_id=current_user.id,
            dataset_id=request.dataset_id,
            stage=1 if last_completed_set is None else (last_completed_set.stage + 1),
            status="active",
            mode=request.mode or "progressive",
            chunk_number=chunk_number,
            total_chunks=total_chunks,
            chunk_size=current_chunk_size,
            total_dataset_size=total_elements,
            # Initialize batch tracking fields with continuation logic
            current_batch_start=next_batch_start,
            current_batch_end=next_batch_end,
            isolation_phase=True,
            mastered_up_to=last_completed_set.current_batch_end if last_completed_set else 0,
            batch_size=batch_size
        )
        db.add(learning_set)
        db.flush()
        
        # Select elements for this chunk
        print(f"DEBUG: Element selection decision - request.force_review={request.force_review}, chunk_number={chunk_number}")
        if request.force_review:
            # For force review, include ALL elements in the dataset
            print(f"DEBUG: Force review - selecting ALL elements")
            elements = db.query(Element).filter(Element.dataset_id == request.dataset_id).order_by(Element.created_at, Element.id).all()
        elif chunk_number:
            # Chunked learning: skip already mastered elements and get new ones
            print(f"DEBUG: Chunked learning - selecting with mastery filter")
            mastered_element_ids = db.query(UserElementReview.element_id).filter(
                and_(
                    UserElementReview.user_id == current_user.id,
                    UserElementReview.status.in_(["isolation_mastered", "integration_confirmed"])
                )
            ).join(Element).filter(Element.dataset_id == request.dataset_id).subquery()
            
            # Get new elements (not yet mastered)
            new_elements = db.query(Element).filter(
                and_(
                    Element.dataset_id == request.dataset_id,
                    ~Element.id.in_(mastered_element_ids)
                )
            ).order_by(Element.created_at, Element.id).limit(current_chunk_size).all()
            
            # Get reinforcement elements from previous chunks
            reinforcement_elements = get_reinforcement_items(
                db, learning_set, config['reinforcement_percentage']
            )
            
            # Combine new and reinforcement elements
            elements = new_elements + reinforcement_elements
            
            # Shuffle to mix reinforcement items throughout
            import random
            random.shuffle(elements)
        else:
            # Regular progressive learning - start with current batch only
            # For batch-based learning, always start with exactly batch_size elements
            print(f"DEBUG: Regular progressive - batch selection")
            print(f"DEBUG: Creating regular progressive learning session")
            print(f"DEBUG: batch_size = {batch_size}")
            print(f"DEBUG: total_elements = {total_elements}")
            print(f"DEBUG: next_batch_start = {learning_set.current_batch_start}")
            print(f"DEBUG: next_batch_end = {learning_set.current_batch_end}")
            
            # Select elements starting from the determined batch position
            elements = db.query(Element).filter(
                Element.dataset_id == request.dataset_id
            ).order_by(Element.created_at, Element.id).offset(learning_set.current_batch_start - 1).limit(
                learning_set.current_batch_end - learning_set.current_batch_start + 1
            ).all()
            
            print(f"DEBUG: Selected {len(elements)} elements for current batch")
            
            # Override the current_chunk_size to match actual selection
            current_chunk_size = len(elements)
        
        # Add elements to the learning set
        print(f"DEBUG: About to add {len(elements)} elements to learning set")
        for i, element in enumerate(elements):
            # Calculate the correct position based on current batch start
            position = learning_set.current_batch_start + i
            item = UserLearningSetItem(
                learning_set_id=learning_set.id,
                element_id=element.id,
                position=position
            )
            db.add(item)
            print(f"DEBUG: Added element at position {position}")
        
        print(f"DEBUG: Learning set created with {len(elements)} items")
        
        db.commit()
        db.refresh(learning_set)
    
    # Check if we're starting a session in spiral review mode
    if learning_set and learning_set.spiral_review_mode:
        spiral_config = config
        cycles = learning_set.completed_integration_cycles or 0
        learning_message = f"🔄 Spiral Review Active: Reinforcing weak cards from positions 1-{learning_set.current_batch_end} after {cycles} integration cycles. Mastering these will strengthen your long-term retention! 💪"
    
    # Always update timer settings from the current request (for both new and existing sessions)
    if request.timer_enabled:
        timer_settings_cache[str(learning_set.id)] = {
            'timer_enabled': request.timer_enabled,
            'timer_seconds': request.timer_seconds or 30,
            'timer_mode': request.timer_mode or "optional"
        }
    else:
        # If timer is disabled, clear any existing timer settings
        timer_settings_cache[str(learning_set.id)] = {
            'timer_enabled': False,
            'timer_seconds': 30,
            'timer_mode': "optional"
        }
    
    # Get timer settings from cache or defaults
    timer_settings = timer_settings_cache.get(str(learning_set.id), {
        'timer_enabled': False,
        'timer_seconds': 30,
        'timer_mode': "optional"
    })
    
    return SessionResponse(
        learning_set_id=learning_set.id,
        dataset_id=learning_set.dataset_id,
        stage=learning_set.stage,
        status=learning_set.status,
        mode=learning_set.mode,
        total_items=len(learning_set.items),
        chunk_number=learning_set.chunk_number,
        total_chunks=learning_set.total_chunks,
        chunk_size=learning_set.chunk_size,
        total_dataset_size=learning_set.total_dataset_size,
        is_chunked_learning=bool(learning_set.chunk_number and learning_set.total_chunks),
        learning_message=learning_message if 'learning_message' in locals() else None,
        timer_enabled=timer_settings['timer_enabled'],
        timer_seconds=timer_settings['timer_seconds'],
        timer_mode=timer_settings['timer_mode']
    )


@router.get("/next", response_model=FlashcardResponse)
async def get_next_flashcard(
    learning_set_id: str,
    force_review: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the next flashcard to review"""
    from datetime import datetime
    request_time = datetime.now().strftime("%H:%M:%S.%f")
    print(f"DEBUG [{request_time}]: Starting get_next_flashcard request for learning_set {learning_set_id}")
    
    # Initialize variables to avoid UnboundLocalError
    element_id = None
    config = get_learning_config(db)
    
    # Verify learning set belongs to user
    learning_set = db.query(UserLearningSet).filter(
        and_(
            UserLearningSet.id == learning_set_id,
            UserLearningSet.user_id == current_user.id
        )
    ).first()
    
    if not learning_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning set not found"
        )    # Get elements in the learning set based on current learning phase
    current_batch_start = learning_set.current_batch_start
    current_batch_end = learning_set.current_batch_end
    is_isolation = learning_set.isolation_phase
    
    # Filter element_ids based on current phase
    if is_isolation:
        # Isolation Phase: Only from current batch
        batch_items = [item for item in learning_set.items 
                       if current_batch_start <= item.position <= current_batch_end]
        element_ids = [item.element_id for item in batch_items]
    else:
        # Integration Phase: Only from mastered positions (1 to mastered_up_to)
        mastered_up_to = learning_set.mastered_up_to
        integration_items = [item for item in learning_set.items 
                            if item.position <= mastered_up_to]  # Use mastered_up_to instead of current_batch_end
        element_ids = [item.element_id for item in integration_items]
    
    # Initialize mastered_count early to avoid scoping issues
    mastered_count = 0
    
    # Priority 0: Spiral Review Mode (highest priority)
    if learning_set.spiral_review_mode:
        # Get spiral review cards for current session
        spiral_cards = get_spiral_review_cards(
            db, current_user.id, learning_set.dataset_id,
            learning_set.current_batch_end, config
        )
        
        if spiral_cards:
            # Select from available spiral cards
            spiral_element_ids = [card.id for card in spiral_cards]
            element_id = random.choice(spiral_element_ids)
            print(f"DEBUG: Spiral review mode - selected card {element_id}")
            # Skip to element retrieval - no need to check other priorities
        else:
            # No more weak cards, exit spiral review mode
            learning_set.spiral_review_mode = False
            db.commit()
            db.refresh(learning_set)
            print("DEBUG: Spiral review completed - no more weak cards")
            # Continue to normal priority selection below
            element_id = None
    else:
        # Normal card selection - not in spiral review mode
        element_id = None
    
    # If not in spiral mode or spiral mode just ended, use normal selection
    if not learning_set.spiral_review_mode and element_id is None:
        
        # FIRST: Check if we should progress to next phase/batch regardless of element selection
        # Check mastery differently for isolation vs integration phase using new classification system
        if learning_set.isolation_phase:
            # Isolation phase: Require all cards in current batch to be isolation mastered or higher
            batch_reviews = db.query(UserElementReview.status).filter(
                and_(
                    UserElementReview.user_id == current_user.id,
                    UserElementReview.element_id.in_(element_ids)
                )
            ).all()
            mastered_in_isolation = sum(1 for (status,) in batch_reviews if status in ["isolation_mastered", "integration_confirmed"])
            batch_ready_for_progression = (len(element_ids) > 0 and mastered_in_isolation == len(element_ids))
            print(f"DEBUG: Isolation phase progression check - isolation mastered or higher {mastered_in_isolation}/{len(element_ids)} in batch")
        else:
            # Integration phase: Require integration confirmation for all eligible cards
            mastered_count = db.query(func.count(UserElementReview.id)).filter(
                and_(
                    UserElementReview.user_id == current_user.id,
                    UserElementReview.element_id.in_(element_ids),
                    UserElementReview.status == "integration_confirmed"
                )
            ).scalar() or 0
            batch_ready_for_progression = (len(element_ids) > 0 and mastered_count >= len(element_ids))
        
        # If batch is ready for progression and not forcing review, check for phase transitions
        if batch_ready_for_progression and not force_review:
            # Check if this is chunked learning
            if learning_set.chunk_number and learning_set.total_chunks:
                # This chunk is complete, check if we need to start the next chunk
                if learning_set.chunk_number < learning_set.total_chunks:
                    # Start next chunk
                    next_chunk_response = await start_next_chunk(db, learning_set, current_user)
                    raise HTTPException(
                        status_code=status.HTTP_200_OK,
                        detail=next_chunk_response
                    )
                else:
                    # All chunks completed
                    learning_set.status = "completed"
                    db.commit()
                    
                    # Update dataset progress
                    await _update_dataset_progress(db, current_user.id)
                    
                    raise HTTPException(
                        status_code=status.HTTP_204_NO_CONTENT,
                        detail="🎉 Congratulations! You've completed the entire dataset! All chunks mastered! 🏆"
                    )
            else:
                # Staged isolation learning - check if current batch is fully mastered
                config = get_learning_config(db)
                
                if learning_set.isolation_phase:
                    # Check if we should switch to integration after completing 2 batches
                    total_dataset_elements = db.query(func.count(Element.id)).filter(
                        Element.dataset_id == learning_set.dataset_id
                    ).scalar() or 0
                    
                    batch_size = config['batch_size']
                    completed_batches = learning_set.current_batch_end // batch_size
                    
                    # After 2nd batch is mastered, switch to integration phase
                    if completed_batches >= 2:
                        print(f"DEBUG: Completed {completed_batches} batches - switching to integration phase")
                        
                        # Switch to integration phase
                        learning_set.isolation_phase = False
                        learning_set.mastered_up_to = learning_set.current_batch_end  # Mark all current cards as available for integration
                        
                        db.commit()
                        db.refresh(learning_set)
                        
                        # Select from integration set (all mastered cards so far)
                        integration_items = [item for item in learning_set.items 
                                           if item.position <= learning_set.mastered_up_to]
                        integration_element_ids = [item.element_id for item in integration_items]
                        
                        if integration_element_ids:
                            element_id = random.choice(integration_element_ids)
                            print(f"DEBUG: Integration phase started - selecting from positions 1-{learning_set.mastered_up_to}")
                    else:
                        # Still in first batch or need to expand to 2nd batch
                        next_batch_start = learning_set.current_batch_end + 1

                        if next_batch_start <= total_dataset_elements:
                            new_batch_end = min(next_batch_start + batch_size - 1, total_dataset_elements)

                            # Mark what has been mastered so far
                            prev_batch_end = learning_set.current_batch_end
                            learning_set.mastered_up_to = prev_batch_end
                            # Expand visible range and keep isolation
                            learning_set.current_batch_end = new_batch_end
                            learning_set.isolation_phase = True

                            # Add new items for the next batch if missing
                            existing_positions = {item.position for item in learning_set.items}
                            needed_positions = [pos for pos in range(next_batch_start, new_batch_end + 1) if pos not in existing_positions]
                            if needed_positions:
                                start_offset = min(needed_positions) - 1
                                new_elements = db.query(Element).filter(
                                    Element.dataset_id == learning_set.dataset_id
                                ).order_by(Element.created_at, Element.id).offset(start_offset).limit(len(needed_positions)).all()
                                for i, element in enumerate(new_elements):
                                    db.add(UserLearningSetItem(
                                        learning_set_id=learning_set.id,
                                        element_id=element.id,
                                        position=needed_positions[i]
                                    ))

                            db.commit()
                            db.refresh(learning_set)

                            # Select a card from the new batch to begin
                            new_batch_element_ids = [item.element_id for item in learning_set.items if item.position >= next_batch_start and item.position <= new_batch_end]
                            if new_batch_element_ids:
                                element_id = random.choice(new_batch_element_ids)
                                print(f"DEBUG: Isolation expanded to batch {completed_batches + 1} (positions {next_batch_start}-{new_batch_end})")
                        else:
                            # No more elements to add: session complete
                            learning_set.status = "completed"
                            db.commit()
                            await _update_dataset_progress(db, current_user.id)
                            raise HTTPException(
                                status_code=status.HTTP_204_NO_CONTENT,
                                detail="🎉 Congratulations! You've completed the entire dataset! All cards mastered! 🏆"
                            )
                    
                else:
                    # Check if integration phase is truly complete (all cards mastered in integration)
                    integration_items = [item for item in learning_set.items 
                                       if item.position <= learning_set.current_batch_end]
                    integration_element_ids = [item.element_id for item in integration_items]
                    
                    integration_mastered = db.query(func.count(UserElementReview.id)).filter(
                        and_(
                            UserElementReview.user_id == current_user.id,
                            UserElementReview.element_id.in_(integration_element_ids),
                            UserElementReview.status == "integration_confirmed"
                        )
                    ).scalar() or 0
                    
                    if integration_mastered < len(integration_element_ids):
                        # Still working on integration - continue reviewing
                        element_id = random.choice(integration_element_ids)
                    else:
                        # END OF INTEGRATION PHASE - Check for spiral review or next batch
                        total_dataset_elements = db.query(func.count(Element.id)).filter(
                            Element.dataset_id == learning_set.dataset_id
                        ).scalar() or 0
                        
                        # Update integration cycle counter
                        learning_set.completed_integration_cycles = (learning_set.completed_integration_cycles or 0) + 1
                        
                        # Check if spiral review should be triggered
                        should_spiral, review_range = should_trigger_spiral_review(
                            db, current_user.id, learning_set.dataset_id,
                            learning_set.current_batch_end, config
                        )
                        
                        if should_spiral:
                            # Trigger spiral review session
                            learning_set.spiral_review_mode = True
                            db.commit()
                            db.refresh(learning_set)
                            
                            # Get spiral review cards for current session
                            spiral_cards = get_spiral_review_cards(
                                db, current_user.id, learning_set.dataset_id,
                                learning_set.current_batch_end, config
                            )
                            
                            if spiral_cards:
                                spiral_element_ids = [card.id for card in spiral_cards]
                                element_id = random.choice(spiral_element_ids)
                                print(f"DEBUG: Starting spiral review mode - selected card {element_id}")
                            else:
                                # No weak cards found, continue normal progression
                                print("DEBUG: No weak cards for spiral review")
                        
                        # If no spiral review triggered, check for next batch expansion  
                        if element_id is None:
                            next_batch_start = learning_set.current_batch_end + 1
                            batch_size = config['batch_size']
                            
                            if next_batch_start <= total_dataset_elements:
                                # Expand to next batch and return to isolation
                                new_batch_end = min(next_batch_start + batch_size - 1, total_dataset_elements)
                                
                                learning_set.current_batch_end = new_batch_end
                                learning_set.isolation_phase = True  # Return to isolation for new batch
                                learning_set.mastered_up_to = new_batch_end - batch_size  # Previous integration end
                                
                                # Add new items to the learning set
                                existing_positions = [item.position for item in learning_set.items]
                                new_positions_needed = []
                                for pos in range(next_batch_start, new_batch_end + 1):
                                    if pos not in existing_positions:
                                        new_positions_needed.append(pos)
                                
                                if new_positions_needed:
                                    start_offset = min(new_positions_needed) - 1
                                    elements_needed = len(new_positions_needed)
                                    
                                    new_elements = db.query(Element).filter(
                                        Element.dataset_id == learning_set.dataset_id
                                    ).order_by(Element.created_at, Element.id).offset(start_offset).limit(elements_needed).all()
                                    
                                    for i, element in enumerate(new_elements):
                                        position = new_positions_needed[i]
                                        new_item = UserLearningSetItem(
                                            learning_set_id=learning_set.id,
                                            element_id=element.id,
                                            position=position
                                        )
                                        db.add(new_item)
                                
                                db.commit()
                                db.refresh(learning_set)
                                
                                # Select first element from new batch for isolation
                                new_batch_element_ids = [item.element_id for item in learning_set.items 
                                                        if item.position >= next_batch_start]
                                if new_batch_element_ids:
                                    element_id = random.choice(new_batch_element_ids)
                                    print(f"DEBUG: Integration complete - starting new isolation batch {next_batch_start}-{new_batch_end}")
                            else:
                                # All batches completed!
                                learning_set.status = "completed"
                                db.commit()
                                
                                await _update_dataset_progress(db, current_user.id)
                                
                                raise HTTPException(
                                    status_code=status.HTTP_204_NO_CONTENT,
                                    detail="🎉 Congratulations! You've completed the entire dataset! All cards mastered! 🏆"
                                )
        
        # If no element selected through phase progression, use normal element selection
        if element_id is None:
            # Priority 1: Due items (spaced repetition)
            # In isolation phase, be more flexible with due times to avoid gaps
            if learning_set.isolation_phase:
                # Isolation phase: Include cards due within 15 minutes to avoid session gaps
                due_threshold = datetime.utcnow() + timedelta(minutes=15)
            else:
                # Integration phase: Use strict due times
                due_threshold = datetime.utcnow()
                
            # Filter cards based on phase
            if learning_set.isolation_phase:
                # Isolation phase: exclude already mastered cards
                excluded_statuses = ["isolation_mastered", "integration_confirmed"]
            else:
                # Integration phase: only exclude fully integrated cards, allow isolation_mastered cards
                excluded_statuses = ["integration_confirmed"]
                
            due_reviews = db.query(UserElementReview).filter(
                and_(
                    UserElementReview.user_id == current_user.id,
                    UserElementReview.element_id.in_(element_ids),
                    UserElementReview.next_due <= due_threshold,
                    ~UserElementReview.status.in_(excluded_statuses)
                )
            ).all()
            
            if due_reviews:
                review = random.choice(due_reviews)
                element_id = review.element_id
            else:
                # Priority 2: New items (never reviewed)
                reviewed_element_ids = db.query(UserElementReview.element_id).filter(
                    and_(
                        UserElementReview.user_id == current_user.id,
                        UserElementReview.element_id.in_(element_ids)
                    )
                ).all()
                reviewed_ids = [r[0] for r in reviewed_element_ids]
                
                new_element_ids = [eid for eid in element_ids if eid not in reviewed_ids]
                
                if new_element_ids:
                    print(f"DEBUG [{request_time}]: Found {len(new_element_ids)} new elements: {new_element_ids}")
                    
                    # Avoid recently attempted elements to prevent immediate repetition
                    recent_attempts = db.query(UserFieldAttempt.element_id).filter(
                        and_(
                            UserFieldAttempt.user_id == current_user.id,
                            UserFieldAttempt.element_id.in_(new_element_ids)
                        )
                    ).order_by(UserFieldAttempt.attempted_at.desc()).limit(3).all()  # Last 3 attempts
                    
                    recent_element_ids = [r[0] for r in recent_attempts]
                    print(f"DEBUG [{request_time}]: Recent element IDs from last 3 attempts: {recent_element_ids}")
                    
                    # Try to select from non-recently-attempted new elements first
                    preferred_new_elements = [eid for eid in new_element_ids if eid not in recent_element_ids]
                    print(f"DEBUG [{request_time}]: Preferred new elements (avoiding recent): {preferred_new_elements}")
                    
                    if preferred_new_elements:
                        element_id = random.choice(preferred_new_elements)
                        print(f"DEBUG [{request_time}]: Selected preferred element: {element_id}")
                    else:
                        # All new elements were recently attempted, pick any new element
                        element_id = random.choice(new_element_ids)
                        print(f"DEBUG [{request_time}]: All elements recently attempted, selected any: {element_id}")
                
                # Priority 3: Any element if we still haven't found one (excluding mastered cards)
                if element_id is None:
                    # Filter out mastered cards from element_ids based on phase
                    if learning_set.isolation_phase:
                        # Isolation phase: exclude already mastered cards
                        excluded_statuses = ["isolation_mastered", "integration_confirmed"]
                    else:
                        # Integration phase: only exclude fully integrated cards, allow isolation_mastered cards
                        excluded_statuses = ["integration_confirmed"]
                    
                    # Filter out mastered cards from element_ids
                    available_reviews = db.query(UserElementReview).filter(
                        and_(
                            UserElementReview.user_id == current_user.id,
                            UserElementReview.element_id.in_(element_ids),
                            ~UserElementReview.status.in_(excluded_statuses)
                        )
                    ).all()
                    
                    if available_reviews:
                        available_element_ids = [review.element_id for review in available_reviews]
                        element_id = random.choice(available_element_ids)
                        print(f"DEBUG [{request_time}]: Selected from available non-mastered elements: {element_id}")
                    else:
                        # Fallback: if all cards in current batch are mastered, select any element
                        # This should trigger phase progression on the next call
                        element_id = random.choice(element_ids)
                        print(f"DEBUG [{request_time}]: All cards mastered, selected any (should trigger progression): {element_id}")
    
    # Validate we have an element to work with
    if element_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No elements available for review"
        )

    # Avoid showing the same element twice in a row (prevents forced reverse direction)
    last_attempt = db.query(UserFieldAttempt.element_id).filter(
        and_(
            UserFieldAttempt.user_id == current_user.id,
            UserFieldAttempt.element_id.in_(element_ids)
        )
    ).order_by(UserFieldAttempt.attempted_at.desc()).first()

    if last_attempt and last_attempt[0] == element_id and len(element_ids) > 1:
        excluded_statuses_now = (
            ["isolation_mastered", "integration_confirmed"]
            if learning_set.isolation_phase else ["integration_confirmed"]
        )
        mastered_now = {
            r.element_id for r in db.query(UserElementReview).filter(
                and_(
                    UserElementReview.user_id == current_user.id,
                    UserElementReview.element_id.in_(element_ids),
                    UserElementReview.status.in_(excluded_statuses_now)
                )
            ).all()
        }
        alternatives = [eid for eid in element_ids if eid != element_id and eid not in mastered_now]
        if alternatives:
            element_id = random.choice(alternatives)
            print(f"DEBUG: Swapped repeated element to avoid back-to-back reverse: {element_id}")

    # Get the selected element from database
    element = db.query(Element).filter(Element.id == element_id).first()
    if not element:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Element not found"
        )
    
    # Get all fields for this element
    fields = db.query(Field).filter(Field.element_id == element_id).all()
    if len(fields) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Element must have at least 2 fields for flashcard creation"
        )
    
    print(f"DEBUG [{request_time}]: About to select fields for element_id: {element_id}")
    
    # Select question and answer fields, avoiding recently attempted combinations
    field_names = [f.field_name for f in fields]
    print(f"DEBUG [{request_time}]: Available field names for element {element_id}: {field_names}")
    
    # Get recent field attempts for this element to avoid immediate repetition
    recent_field_attempts = db.query(UserFieldAttempt).filter(
        and_(
            UserFieldAttempt.user_id == current_user.id,
            UserFieldAttempt.element_id == element_id
        )
    ).order_by(UserFieldAttempt.attempted_at.desc()).limit(5).all()  # Check last 5 attempts
    
    # Get recently used field combinations (question_field, answer_field pairs)
    recent_combinations = [(attempt.question_field, attempt.answer_field) for attempt in recent_field_attempts]
    print(f"DEBUG: Recent field combinations for element {element_id}: {recent_combinations}")
    
    # Generate all possible field combinations
    possible_combinations = []
    for q_field in field_names:
        for a_field in field_names:
            if q_field != a_field:  # Question and answer must be different fields
                possible_combinations.append((q_field, a_field))
    
    print(f"DEBUG: All possible combinations: {possible_combinations}")
    
    # Filter out recently used combinations
    available_combinations = [combo for combo in possible_combinations if combo not in recent_combinations]
    print(f"DEBUG: Available combinations (after filtering recent): {available_combinations}")
    
    # If no combinations are available (all were recently used), use all combinations
    if not available_combinations:
        available_combinations = possible_combinations
        print(f"DEBUG: No available combinations, using all: {available_combinations}")
    
    # Select a random available combination
    if available_combinations:
        question_field_name, answer_field_name = random.choice(available_combinations)
        print(f"DEBUG: Selected combination: question='{question_field_name}', answer='{answer_field_name}'")
    else:
        # Fallback to original logic if no valid combinations found
        question_field_name = random.choice(field_names)
        answer_field_name = random.choice([f for f in field_names if f != question_field_name])
        print(f"DEBUG: Fallback selection: question='{question_field_name}', answer='{answer_field_name}'")
    
    question_field = next(f for f in fields if f.field_name == question_field_name)
    answer_field = next(f for f in fields if f.field_name == answer_field_name)
    
    # Validate that question and answer fields have values
    if not question_field.field_value or question_field.field_value.strip() == "":
        # Try to find another field with a value
        valid_fields = [f for f in fields if f.field_value and f.field_value.strip() != ""]
        if len(valid_fields) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Element does not have enough fields with valid values for flashcard creation"
            )
        # Reassign question and answer fields
        question_field = valid_fields[0]
        answer_field = valid_fields[1] if valid_fields[1] != question_field else valid_fields[0]
        question_field_name = question_field.field_name
        answer_field_name = answer_field.field_name
    
    if not answer_field.field_value or answer_field.field_value.strip() == "":
        # Try to find another field with a value  
        valid_fields = [f for f in fields if f.field_value and f.field_value.strip() != "" and f != question_field]
        if not valid_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Element does not have enough fields with valid values for flashcard creation"
            )
        answer_field = valid_fields[0]
        answer_field_name = answer_field.field_name
    
    # Get current learning configuration for distractor count
    config = get_learning_config(db)
    distractor_count = config['distractor_count']
    
    # Generate distractors using same scope as card selection for distractors
    if learning_set.isolation_phase:
        # Isolation Phase: Distractors only from current batch
        batch_element_ids = [item.element_id for item in learning_set.items 
                            if learning_set.current_batch_start <= item.position <= learning_set.current_batch_end]
        distractor_element_ids = [eid for eid in batch_element_ids if eid != element_id]
    else:
        # Integration Phase: Distractors from all available cards
        integration_element_ids = [item.element_id for item in learning_set.items 
                                  if item.position <= learning_set.current_batch_end]
        distractor_element_ids = [eid for eid in integration_element_ids if eid != element_id]

    # Use distractor_element_ids in the query instead of all learning set items
    distractor_fields = db.query(Field).filter(
        and_(
            Field.element_id.in_(distractor_element_ids),
            Field.element_id != element_id,  # Exclude current element
            Field.field_name == answer_field_name
        )
    ).limit(distractor_count).all()
    
    # Create answer choices
    choices = [answer_field.field_value]
    choices.extend([d.field_value for d in distractor_fields])
    random.shuffle(choices)
    
    # Ensure we have at least 2 choices (correct + 1 distractor) and max 4 choices
    max_choices = min(4, distractor_count + 1)
    choices = choices[:max_choices]
    
    # Get timer settings from cache
    timer_settings = timer_settings_cache.get(str(learning_set.id), {
        'timer_enabled': False,
        'timer_seconds': 30,
        'timer_mode': "optional"
    })
    
    # Get FSRS statistics for this element
    review = db.query(UserElementReview).filter(
        and_(
            UserElementReview.user_id == current_user.id,
            UserElementReview.element_id == element_id
        )
    ).first()
    
    fsrs_stats = None
    if review:
        # Calculate days until next due
        days_until_due = 0
        if review.next_due:
            # Ensure both datetimes have the same timezone awareness
            current_time = datetime.utcnow()
            next_due = review.next_due
            
            # If next_due is timezone-aware and current_time is naive, make current_time timezone-aware
            if next_due.tzinfo is not None and current_time.tzinfo is None:
                from datetime import timezone
                current_time = current_time.replace(tzinfo=timezone.utc)
            # If current_time is timezone-aware and next_due is naive, make next_due timezone-aware
            elif current_time.tzinfo is not None and next_due.tzinfo is None:
                from datetime import timezone
                next_due = next_due.replace(tzinfo=timezone.utc)
            
            time_diff = next_due - current_time
            days_until_due = max(0, time_diff.days)
        
        fsrs_stats = {
            "review_count": review.review_count or 0,
            "success_streak": review.success_streak or 0,
            "ease_factor": round((review.ease_factor or 250) / 100.0, 2),  # Convert to decimal
            "interval_days": review.interval_days or 1,
            "days_until_due": days_until_due,
            "stability_score": round(review.stability_score or 1.0, 2),
            "status": review.status or "new",
            "accuracy_percentage": round((review.accuracy_percentage or 0.0) * 100, 1),  # Convert to percentage
            "is_difficult": review.is_difficult or False,
            "integration_confirmed": review.integration_confirmed or False,
            "integration_attempts": review.integration_attempts or 0
        }
    else:
        # New card - no review history
        fsrs_stats = {
            "review_count": 0,
            "success_streak": 0,
            "ease_factor": 2.5,  # Default ease factor
            "interval_days": 1,
            "days_until_due": 0,
            "stability_score": 1.0,  # Default stability
            "status": "new",
            "accuracy_percentage": 0.0,
            "is_difficult": False,
            "integration_confirmed": False,
            "integration_attempts": 0
        }
    
    return FlashcardResponse(
        element_id=element_id,
        question_field=question_field_name,
        question_value=question_field.field_value,
        question_type=question_field.field_type,
        question_media_url=question_field.media_url,
        answer_field=answer_field_name,
        choices=choices,
        correct_answer=answer_field.field_value,
        timer_enabled=timer_settings['timer_enabled'],
        timer_seconds=timer_settings['timer_seconds'] if timer_settings['timer_enabled'] else None,
        timer_mode=timer_settings['timer_mode'],
        fsrs_stats=fsrs_stats
    )


def calculate_timer_performance(response_time_ms: Optional[int], timer_seconds: int, timer_expired: bool, was_timed: bool):
    """Calculate timer performance feedback and bonus points"""
    if not was_timed or response_time_ms is None:
        return None, 0
    
    if timer_expired:
        return "expired", 0
    
    # Calculate performance thresholds
    total_time_ms = timer_seconds * 1000
    fast_threshold = total_time_ms * 0.3    # < 30% = fast
    good_threshold = total_time_ms * 0.7    # < 70% = good
    
    if response_time_ms < fast_threshold:
        performance = "fast"
        bonus = 20  # 20 point bonus for fast answers
    elif response_time_ms < good_threshold:
        performance = "good"
        bonus = 10  # 10 point bonus for good answers
    else:
        performance = "slow"
        bonus = 0   # No bonus for slow answers
    
    return performance, bonus


async def _trigger_gamification_updates(db: Session, user_id, new_status: str):
    """Update streak, badges, and leaderboard scores after answering a card.

    Called fire-and-forget from submit_answer; any exception is swallowed by
    the caller so gamification failures never break the answer response.
    """
    today = date.today()

    # 1. Streak — create or advance/reset based on last activity date
    streak = db.query(UserStreak).filter(UserStreak.user_id == user_id).first()
    if not streak:
        streak = UserStreak(
            user_id=user_id,
            current_streak=1,
            max_streak=1,
            last_activity=datetime.utcnow(),
        )
        db.add(streak)
    else:
        last_date = streak.last_activity.date() if streak.last_activity else None
        if last_date != today:
            if last_date == today - timedelta(days=1):
                streak.current_streak += 1
                streak.max_streak = max(streak.max_streak, streak.current_streak)
            else:
                streak.current_streak = 1
            streak.last_activity = datetime.utcnow()

    # 2. Streak badges
    await _check_streak_badges(db, user_id, streak.current_streak)

    # 3. Mastery badges — only on graduation events
    if new_status in ("isolation_mastered", "integration_confirmed"):
        await check_mastery_badges(db, user_id)

    # 4. Leaderboard scores: mastered card count and best streak
    mastered_count = db.query(func.count(UserElementReview.id)).filter(
        and_(
            UserElementReview.user_id == user_id,
            UserElementReview.status.in_(["isolation_mastered", "integration_confirmed"]),
        )
    ).scalar() or 0

    await _update_score(db, user_id, "mastered", mastered_count)
    await _update_score(db, user_id, "streak", streak.max_streak)

    # Sessions score
    sessions_count = db.query(func.count(UserLearningSet.id)).filter(
        UserLearningSet.user_id == user_id
    ).scalar() or 0
    await _update_score(db, user_id, "sessions", sessions_count)

    # Accuracy score (0–100 integer)
    total_attempts = db.query(func.count(UserFieldAttempt.id)).filter(
        UserFieldAttempt.user_id == user_id
    ).scalar() or 0
    correct_attempts = db.query(func.count(UserFieldAttempt.id)).filter(
        and_(UserFieldAttempt.user_id == user_id, UserFieldAttempt.is_correct == True)
    ).scalar() or 0
    accuracy_int = round(correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
    await _update_score(db, user_id, "accuracy", accuracy_int)

    db.commit()

    # Keep UserGameStats in sync (consolidates the two leaderboard systems)
    RankingService(db).calculate_user_statistics(str(user_id))


@router.post("/answer", response_model=AnswerSubmissionResponse)
async def submit_answer(
    request: AnswerSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit an answer and update review data"""
    # Record the attempt
    attempt = UserFieldAttempt(
        user_id=current_user.id,
        element_id=request.element_id,
        question_field=request.question_field,
        answer_field=request.answer_field,
        user_answer=request.user_answer,
        correct_answer=request.correct_answer,
        is_correct=request.is_correct,
        response_time_ms=request.response_time_ms
    )
    db.add(attempt)
    db.flush()  # Flush to make the new attempt visible to subsequent queries
    
    # Update or create review record
    review = db.query(UserElementReview).filter(
        and_(
            UserElementReview.user_id == current_user.id,
            UserElementReview.element_id == request.element_id
        )
    ).first()
    
    if not review:
        review = UserElementReview(
            user_id=current_user.id,
            element_id=request.element_id,
            success_streak=0,
            review_count=0,
            status="new",
            ease_factor=250  # 2.5 * 100
        )
        db.add(review)
    
    # Get the learning set to check if this is a force review session
    learning_set = db.query(UserLearningSet).filter(
        and_(
            UserLearningSet.user_id == current_user.id,
            UserLearningSet.items.any(UserLearningSetItem.element_id == request.element_id)
        )
    ).first()
    
    is_force_review = learning_set and learning_set.mode == "force_review"
    
    # Get current learning configuration and classification config
    config = get_learning_config(db)
    integration_config = get_integration_config(db)
    classification_config = get_classification_config(db)
    
    # Get dynamic mastery window based on dataset field count and learning phase
    dataset_id = db.query(Element).filter(Element.id == request.element_id).first().dataset_id
    dynamic_mastery_window = get_dynamic_mastery_window(db, dataset_id, learning_set, integration_config)
    
    # Update review based on answer
    review.review_count += 1
    review.last_reviewed = datetime.utcnow()

    # Get recent attempts within the dynamic window (phase-aware)
    # Cards still in "learning" status always need the full isolation window to qualify for promotion,
    # even if the learning set has moved to integration phase.
    card_status = review.status if review else "new"
    if learning_set and not learning_set.isolation_phase and card_status not in ("learning", "new"):
        # Integration phase for already-promoted cards: Use integration-specific window
        limit = integration_config.get('integration_mastery_window', 1)
    else:
        # Isolation phase, OR card is still in learning/new (needs larger window to assess)
        limit = dynamic_mastery_window

    recent_attempts = db.query(UserFieldAttempt).filter(
        and_(
            UserFieldAttempt.user_id == current_user.id,
            UserFieldAttempt.element_id == request.element_id
        )
    ).order_by(UserFieldAttempt.attempted_at.desc()).limit(limit).all()

    # Update attempts counter and accuracy
    if recent_attempts:
        correct_attempts = sum(1 for attempt in recent_attempts if attempt.is_correct)
        review.accuracy_percentage = correct_attempts / len(recent_attempts)
        review.attempts_in_window = len(recent_attempts)
    
    # Update integration timestamp if we're in integration phase
    if learning_set and not learning_set.isolation_phase:
        review.last_integration_attempt = datetime.utcnow()

    # Use new configurable classification system
    old_status = review.status
    update_card_classification(db, review, recent_attempts, learning_set)
    new_status = review.status
    
    # Check if card achieved mastery through classification system
    is_mastered = new_status in ["isolation_mastered", "integration_confirmed"]

    # --- FSRS scheduling ---------------------------------------------------
    fsrs_cfg = get_fsrs_config(db, current_user.id)
    fsrs = FSRSAlgorithm(
        desired_retention=fsrs_cfg['desired_retention'],
        maximum_interval=fsrs_cfg['maximum_interval'],
    )
    rating = compute_fsrs_rating(
        is_correct=request.is_correct,
        response_time_ms=request.response_time_ms or 5000,
        fast_threshold_ms=fsrs_cfg['fast_threshold_ms'],
        slow_threshold_ms=fsrs_cfg['slow_threshold_ms'],
    )

    in_isolation = bool(learning_set and learning_set.isolation_phase
                        and new_status not in ["isolation_mastered", "integration_confirmed"])

    if in_isolation:
        # Task 6 fix: do NOT advance FSRS state while in isolation phase.
        # Short next_due overrides keep cards in active circulation; real
        # spaced intervals only begin once a card enters integration.
        # Initialise stability/difficulty on the very first answer so the
        # card has a valid state when it graduates.
        if review.review_count == 1:
            review.stability_score = fsrs.initial_stability(rating)
            review.difficulty = fsrs.initial_difficulty(rating)

        # Streak: increment on any non-Again rating, reset on Again
        if rating >= 2:
            review.success_streak += 1
        else:
            review.success_streak = 0
            review.is_difficult = True

        # Short next_due overrides (real spacing starts in integration)
        if review.success_streak < 2:
            review.next_due = datetime.utcnow() + timedelta(minutes=10)
        elif review.success_streak < 4:
            review.next_due = datetime.utcnow() + timedelta(hours=1)
        else:
            review.next_due = datetime.utcnow() + timedelta(days=1)

    else:
        # Integration phase or already mastered: full FSRS update
        elapsed_days = 0.0
        if review.last_reviewed:
            elapsed_days = max(
                (datetime.utcnow() - review.last_reviewed).total_seconds() / 86400.0,
                0.0
            )

        stability = review.stability_score or fsrs.initial_stability(rating)
        difficulty = review.difficulty or fsrs.initial_difficulty(rating)

        new_stability, new_difficulty, interval = fsrs.review(
            stability=stability,
            difficulty=difficulty,
            elapsed_days=elapsed_days,
            rating=rating,
        )

        review.stability_score = new_stability
        review.difficulty = new_difficulty
        review.interval_days = interval

        if rating >= 2:
            review.success_streak += 1
        else:
            review.success_streak = 0
            review.is_difficult = True

        review.next_due = datetime.utcnow() + timedelta(days=interval)
    # --- end FSRS ----------------------------------------------------------
    
    review.updated_at = datetime.utcnow()
    
    # Check if force review session is complete and reset mode
    if is_force_review and new_status in ["isolation_mastered", "integration_confirmed"]:
        element_ids = [item.element_id for item in learning_set.items]
        mastered_count = db.query(func.count(UserElementReview.id)).filter(
            and_(
                UserElementReview.user_id == current_user.id,
                UserElementReview.element_id.in_(element_ids),
                UserElementReview.status.in_(["isolation_mastered", "integration_confirmed"])
            )
        ).scalar() or 0
        
        # If all elements are mastered, reset the mode to progressive
        if mastered_count >= len(element_ids):
            learning_set.mode = "progressive"
    
    # Calculate timer performance and bonus
    timer_performance = None
    time_bonus = 0
    if request.was_timed:
        # Get timer settings for this learning set
        timer_settings = timer_settings_cache.get(str(learning_set.id), {})
        if timer_settings:
            timer_performance, time_bonus = calculate_timer_performance(
                request.response_time_ms,
                timer_settings.get('timer_seconds', 30),
                request.timer_expired,
                request.was_timed
            )
    
    db.commit()

    # Gamification: streak, badges, leaderboard — must never crash the response
    try:
        await _trigger_gamification_updates(db, current_user.id, new_status)
    except Exception:
        pass

    # Update dataset progress if element achieved mastery
    if new_status in ["isolation_mastered", "integration_confirmed"]:
        await _update_dataset_progress(db, current_user.id)
        
        # If in integration, check if all eligible cards are confirmed to expand next batch
        if learning_set and not learning_set.isolation_phase:
            integration_items = [item for item in learning_set.items if item.position <= learning_set.current_batch_end]
            integration_element_ids = [item.element_id for item in integration_items]
            confirmed_count = db.query(func.count(UserElementReview.id)).filter(
                and_(
                    UserElementReview.user_id == current_user.id,
                    UserElementReview.element_id.in_(integration_element_ids),
                    UserElementReview.status == "integration_confirmed"
                )
            ).scalar() or 0
            if confirmed_count >= len(integration_element_ids):
                # Expand to next batch if available
                total_dataset_elements = db.query(func.count(Element.id)).filter(
                    Element.dataset_id == learning_set.dataset_id
                ).scalar() or 0
                next_batch_start = learning_set.current_batch_end + 1
                batch_size = learning_set.batch_size or config.get('batch_size', 5)
                if next_batch_start <= total_dataset_elements:
                    new_batch_end = min(next_batch_start + batch_size - 1, total_dataset_elements)
                    learning_set.current_batch_end = new_batch_end
                    learning_set.isolation_phase = True
                    learning_set.mastered_up_to = new_batch_end - batch_size
                    # Add new items if missing
                    existing_positions = {item.position for item in learning_set.items}
                    needed_positions = [pos for pos in range(next_batch_start, new_batch_end + 1) if pos not in existing_positions]
                    if needed_positions:
                        start_offset = min(needed_positions) - 1
                        new_elements = db.query(Element).filter(
                            Element.dataset_id == learning_set.dataset_id
                        ).order_by(Element.created_at, Element.id).offset(start_offset).limit(len(needed_positions)).all()
                        for i, element in enumerate(new_elements):
                            db.add(UserLearningSetItem(
                                learning_set_id=learning_set.id,
                                element_id=element.id,
                                position=needed_positions[i]
                            ))
                    db.commit()
    
    # Create explanation with accuracy and timer feedback
    accuracy_text = f"Accuracy: {review.accuracy_percentage:.1%}" if review.accuracy_percentage > 0 else "Building accuracy..."
    phase_text = "Isolation" if (learning_set and learning_set.isolation_phase) else "Integration"
    status_display = {
        "learning": "Learning",
        "isolation_mastered": "Mastered",
        "integration_review": "Reviewing",
        "integration_confirmed": "Confirmed", 
        "spiral_review": "Reinforcing"
    }.get(new_status, new_status.title())
    
    explanation = f"{status_display} | {accuracy_text} ({phase_text}), Streak: {review.success_streak}"
    if timer_performance:
        performance_messages = {
            "fast": "⚡ Lightning fast!",
            "good": "👍 Good timing!",
            "slow": "🐌 Take your time next time",
            "expired": "⏰ Time's up!"
        }
        if time_bonus > 0:
            explanation += f" | {performance_messages.get(timer_performance, '')} +{time_bonus} bonus points!"
        else:
            explanation += f" | {performance_messages.get(timer_performance, '')}"
    
    return AnswerSubmissionResponse(
        correct=request.is_correct,
        success_streak=review.success_streak,
        next_due=review.next_due,
        status=review.status,
        explanation=explanation,
        timer_performance=timer_performance,
        time_bonus=time_bonus
    )


@router.get("/progress", response_model=ProgressResponse)
async def get_session_progress(
    learning_set_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get progress for the current learning session"""
    # Verify learning set
    learning_set = db.query(UserLearningSet).filter(
        and_(
            UserLearningSet.id == learning_set_id,
            UserLearningSet.user_id == current_user.id
        )
    ).first()
    
    if not learning_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning set not found"
        )
    
    # Calculate progress based on current batch and phase
    if learning_set.isolation_phase:
        # Show progress within current batch only
        batch_elements = [item.element_id for item in learning_set.items 
                         if learning_set.current_batch_start <= item.position <= learning_set.current_batch_end]
        element_ids = batch_elements
        phase_message = f"Isolation Phase - Batch {learning_set.current_batch_start}-{learning_set.current_batch_end}"
    else:
        # Show progress across all available batches  
        available_elements = [item.element_id for item in learning_set.items 
                             if item.position <= learning_set.current_batch_end]
        element_ids = available_elements
        phase_message = f"Integration Phase - Cards 1-{learning_set.current_batch_end}"
    
    # Get review statistics for current scope
    reviews = db.query(UserElementReview).filter(
        and_(
            UserElementReview.user_id == current_user.id,
            UserElementReview.element_id.in_(element_ids)
        )
    ).all()
    
    # Calculate progress counts using new status system
    mastered_statuses = ["isolation_mastered", "integration_confirmed"]
    mastered_count = len([r for r in reviews if r.status in mastered_statuses])
    due_count = len([r for r in reviews if r.next_due and r.next_due <= datetime.now(timezone.utc)])
    new_count = len(element_ids) - len(reviews)
    
    # Calculate confidence categories for enhanced progress display using new status system
    strong_cards = [r for r in reviews if r.status in ["isolation_mastered", "integration_confirmed"]]
    weak_cards = [r for r in reviews if r.status in ["learning", "integration_review", "spiral_review"] or r.is_difficult]
    review_cards = [r for r in reviews if r.status == "integration_review"]
    new_cards_count = len(element_ids) - len(reviews)
    
    # Configurable classification system statistics
    learning_cards = len([r for r in reviews if r.status == "learning"])
    isolation_mastered = len([r for r in reviews if r.status == "isolation_mastered"])
    integration_review = len([r for r in reviews if r.status == "integration_review"])
    integration_confirmed = len([r for r in reviews if r.status == "integration_confirmed"])
    spiral_review = len([r for r in reviews if r.status == "spiral_review"])
    
    # Calculate integration efficiency (percentage of cards confirmed without review phase)
    integration_eligible = [r for r in reviews if r.status in ["integration_confirmed", "integration_review"] or 
                           getattr(r, 'integration_attempts', 0) > 0]
    successful_confirmations = len([r for r in integration_eligible if r.status == "integration_confirmed"])
    integration_efficiency = (successful_confirmations / len(integration_eligible) * 100) if integration_eligible else 0.0
    
    # Phase description with configurable classification awareness
    if learning_set.isolation_phase:
        phase_description = f"Isolation Phase - Learning batch {learning_set.current_batch_start}-{learning_set.current_batch_end}"
    else:
        phase_description = f"Integration Phase - Confirming mastery of cards 1-{learning_set.current_batch_end}"
    
    # Stability scoring metrics
    stability_scores = [getattr(r, 'stability_score', 1.0) for r in reviews if getattr(r, 'stability_score', None) is not None]
    average_stability_score = sum(stability_scores) / len(stability_scores) if stability_scores else 0.0
    high_stability_count = len([s for s in stability_scores if s > 2.0])
    low_stability_count = len([s for s in stability_scores if s < 1.0])
    
    # Update strong/weak classification for configurable system
    strong_cards_classified = [r for r in reviews if r.status in ["isolation_mastered", "integration_confirmed"]]
    weak_cards_classified = [r for r in reviews if r.status in ["learning", "integration_review", "spiral_review"] or r.is_difficult]
    
    # Determine learning phase based on mastery progress
    total_cards = len(element_ids)
    strong_percentage = len(strong_cards_classified) / total_cards * 100 if total_cards > 0 else 0
    
    if strong_percentage == 100:
        learning_phase = "complete"
    elif strong_percentage >= 80:
        learning_phase = "mastering"
    elif strong_percentage >= 40:
        learning_phase = "building"
    else:
        learning_phase = "learning"
    
    # Get current learning configuration
    config = get_learning_config(db)
    
    # In batch-based flow, we don't use stage-based unlocks; keep flag false to avoid misleading UI
    ready_for_next_stage = False
    
    # Calculate session-level accuracy from UserFieldAttempt records
    from ..sessions.models import UserFieldAttempt
    
    # Get all field attempts for elements in this learning session
    session_attempts = db.query(UserFieldAttempt).filter(
        and_(
            UserFieldAttempt.user_id == current_user.id,
            UserFieldAttempt.element_id.in_(element_ids)
        )
    ).all()
    
    total_questions = len(session_attempts)
    correct_answers = len([attempt for attempt in session_attempts if attempt.is_correct])
    accuracy_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0.0
    
    return ProgressResponse(
        stage=learning_set.stage,
        total_items=len(element_ids),
        mastered_count=mastered_count,
        due_count=due_count,
        new_count=new_count,
        ready_for_next_stage=ready_for_next_stage,
        # Enhanced confidence-based fields using new classification system
        strong_count=len(strong_cards_classified),
        weak_count=len(weak_cards_classified),
        question_count=total_questions,
        learning_phase=learning_phase,
        # Session-level accuracy tracking
        correct_answers=correct_answers,
        total_questions=total_questions,
        accuracy_percentage=round(accuracy_percentage, 1),
        # Configurable Classification fields
        isolation_mastered_count=isolation_mastered,
        integration_confirmed_count=integration_confirmed,
        integration_review_count=integration_review,
        phase_description=phase_description,
        integration_efficiency=round(integration_efficiency, 1),
        # Additional classification status counts
        learning_count=learning_cards,
        spiral_review_count=spiral_review,
        # Stability scoring metrics
        average_stability_score=round(average_stability_score, 2),
        high_stability_count=high_stability_count,
        low_stability_count=low_stability_count
    )


@router.post("/advance-stage")
async def advance_to_next_stage(
    learning_set_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Advance to the next stage by adding more elements"""
    learning_set = db.query(UserLearningSet).filter(
        and_(
            UserLearningSet.id == learning_set_id,
            UserLearningSet.user_id == current_user.id
        )
    ).first()
    
    if not learning_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning set not found"
        )
    
    current_element_ids = [item.element_id for item in learning_set.items]
    
    # Get current learning configuration
    config = get_learning_config(db)
    
    # Get the appropriate stage increment for this learning set
    stage_increment = get_stage_increment_for_learning_set(learning_set, config)
    
    # Get new elements to add
    new_elements = db.query(Element).filter(
        and_(
            Element.dataset_id == learning_set.dataset_id,
            ~Element.id.in_(current_element_ids)
        )
    ).order_by(Element.created_at, Element.id).limit(stage_increment).all()
    
    # Add new elements
    for element in new_elements:
        item = UserLearningSetItem(
            learning_set_id=learning_set.id,
            element_id=element.id,
            position=len(learning_set.items) + 1
        )
        db.add(item)
    
    # Update stage
    learning_set.stage += 1
    learning_set.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": f"Advanced to stage {learning_set.stage}",
        "new_elements_added": len(new_elements),
        "total_elements": len(learning_set.items) + len(new_elements)
    }


@router.get("/{learning_set_id}/confidence-stats")
async def get_confidence_statistics(
    learning_set_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed confidence-based statistics for a learning session"""
    learning_set = db.query(UserLearningSet).filter(
        and_(
            UserLearningSet.id == learning_set_id,
            UserLearningSet.user_id == current_user.id
        )
    ).first()
    
    if not learning_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning set not found"
        )
    
    # Get all element IDs in this learning set
    element_ids = [item.element_id for item in learning_set.items]
    
    # Get review data for all elements
    reviews = db.query(UserElementReview).filter(
        and_(
            UserElementReview.user_id == current_user.id,
            UserElementReview.element_id.in_(element_ids)
        )
    ).all()
    
    # Calculate confidence categories with detailed breakdown
    strong_cards = [r for r in reviews if r.status in ("isolation_mastered", "integration_confirmed")]
    # Every reviewed card that is not mastered is weak (covers learning, new-with-record, difficult, etc.)
    weak_cards = [r for r in reviews if r.status not in ("isolation_mastered", "integration_confirmed")]
    new_cards_count = len(element_ids) - len(reviews)
    
    # Calculate learning phase
    total_cards = len(element_ids)
    strong_percentage = len(strong_cards) / total_cards * 100 if total_cards > 0 else 0
    
    if strong_percentage == 100:
        learning_phase = "complete"
        phase_message = "Practice complete!"
        phase_icon = "✅"
    elif strong_percentage >= 80:
        learning_phase = "mastering"
        phase_message = "Almost there"
        phase_icon = "🎯"
    elif strong_percentage >= 40:
        learning_phase = "building"
        phase_message = "Building mastery"
        phase_icon = "💪"
    else:
        learning_phase = "learning"
        phase_message = "Learning new cards"
        phase_icon = "📚"
    
    # Get detailed card statistics
    difficult_cards = [r for r in reviews if r.is_difficult]
    learning_cards = [r for r in reviews if r.status == "learning"]
    due_cards = [r for r in reviews if r.next_due and r.next_due <= datetime.now(timezone.utc)]
    
    # Calculate average success streak for mastered cards
    avg_success_streak = 0
    if strong_cards:
        avg_success_streak = sum(r.success_streak for r in strong_cards) / len(strong_cards)
    
    return {
        "learning_set_id": learning_set_id,
        "total_cards": total_cards,
        "confidence_breakdown": {
            "strong_count": len(strong_cards),
            "weak_count": len(weak_cards), 
            "new_count": new_cards_count,
            "difficult_count": len(difficult_cards),
            "learning_count": len(learning_cards),
            "due_count": len(due_cards)
        },
        "learning_phase": {
            "phase": learning_phase,
            "message": phase_message,
            "icon": phase_icon,
            "progress_percentage": strong_percentage
        },
        "statistics": {
            "mastery_percentage": strong_percentage,
            "avg_success_streak": round(avg_success_streak, 1),
            "cards_need_review": len(due_cards),
            "difficult_cards": len(difficult_cards)
        },
        "is_force_review": learning_set.mode == "force_review"
    }


@router.get("/fsrs-stats/{learning_set_id}", response_model=FSRSIntegrationStats)
async def get_fsrs_integration_stats(
    learning_set_id: str,
    include_card_details: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive FSRS integration statistics for a learning set"""
    # Verify learning set access
    learning_set = db.query(UserLearningSet).filter(
        and_(
            UserLearningSet.id == learning_set_id,
            UserLearningSet.user_id == current_user.id
        )
    ).first()
    
    if not learning_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning set not found"
        )
    
    # Get all reviews for this learning set
    if learning_set.isolation_phase:
        element_ids = [item.element_id for item in learning_set.items 
                      if learning_set.current_batch_start <= item.position <= learning_set.current_batch_end]
        current_phase = "isolation"
        phase_description = f"Isolation Phase - Batch {learning_set.current_batch_start}-{learning_set.current_batch_end}"
    else:
        element_ids = [item.element_id for item in learning_set.items 
                      if item.position <= learning_set.current_batch_end]
        current_phase = "integration"
        phase_description = f"Integration Phase - Cards 1-{learning_set.current_batch_end}"
    
    reviews = db.query(UserElementReview).filter(
        and_(
            UserElementReview.user_id == current_user.id,
            UserElementReview.element_id.in_(element_ids)
        )
    ).all()
    
    # Calculate basic counts
    total_cards = len(element_ids)
    mastered_count = len([r for r in reviews if r.status in ("isolation_mastered", "integration_confirmed")])
    isolation_mastered_count = len([r for r in reviews if r.status == "isolation_mastered"])
    integration_confirmed_count = len([r for r in reviews if r.status == "integration_confirmed"])
    integration_review_count = len([r for r in reviews if r.status == "integration_review"])
    learning_count = len([r for r in reviews if r.status == "learning"])
    
    # Calculate integration efficiency metrics
    integration_attempts = [r for r in reviews if getattr(r, 'integration_attempts', 0) > 0]
    successful_first_attempts = len([r for r in integration_attempts if getattr(r, 'integration_confirmed', False) and getattr(r, 'integration_attempts', 0) == 1])
    
    integration_efficiency = (successful_first_attempts / len(integration_attempts) * 100) if integration_attempts else 0.0
    first_attempt_success_rate = integration_efficiency
    
    # Calculate average integration attempts for cards that have attempted integration
    total_integration_attempts = sum(getattr(r, 'integration_attempts', 0) for r in integration_attempts)
    average_integration_attempts = total_integration_attempts / len(integration_attempts) if integration_attempts else 0.0
    
    # Calculate reconsolidation rate (cards that returned to isolation after integration failure)
    reconsolidated_cards = len([r for r in reviews if getattr(r, 'integration_attempts', 0) >= 3 and r.status == "learning"])
    reconsolidation_rate = (reconsolidated_cards / len(integration_attempts) * 100) if integration_attempts else 0.0
    
    # Calculate stability statistics
    stability_scores = [getattr(r, 'stability_score', 1.0) for r in reviews if getattr(r, 'stability_score', None) is not None]
    
    if stability_scores:
        stability_scores.sort()
        median_stability = stability_scores[len(stability_scores) // 2]
        average_stability = sum(stability_scores) / len(stability_scores)
        min_stability = min(stability_scores)
        max_stability = max(stability_scores)
        
        high_stability_count = len([s for s in stability_scores if s > 2.0])
        medium_stability_count = len([s for s in stability_scores if 1.0 <= s <= 2.0])
        low_stability_count = len([s for s in stability_scores if s < 1.0])
    else:
        median_stability = average_stability = min_stability = max_stability = 0.0
        high_stability_count = medium_stability_count = low_stability_count = 0
    
    stability_stats = StabilityStats(
        average_stability=round(average_stability, 2),
        median_stability=round(median_stability, 2),
        min_stability=round(min_stability, 2),
        max_stability=round(max_stability, 2),
        high_stability_count=high_stability_count,
        medium_stability_count=medium_stability_count,
        low_stability_count=low_stability_count
    )
    
    # Calculate session timing
    session_start_time = learning_set.created_at
    last_activity_time = max([r.last_reviewed for r in reviews if r.last_reviewed], default=None)
    total_session_time_minutes = None
    if session_start_time and last_activity_time:
        total_session_time_minutes = (last_activity_time - session_start_time).total_seconds() / 60
    
    # Optionally include detailed card information
    card_details = None
    if include_card_details:
        card_details = []
        for review in reviews:
            card_details.append(IntegrationCardDetail(
                element_id=review.element_id,
                status=review.status,
                integration_confirmed=getattr(review, 'integration_confirmed', False),
                integration_attempts=getattr(review, 'integration_attempts', 0),
                stability_score=getattr(review, 'stability_score', 1.0),
                last_integration_attempt=getattr(review, 'last_integration_attempt', None),
                accuracy_percentage=review.accuracy_percentage,
                review_count=review.review_count,
                is_difficult=review.is_difficult
            ))
    
    return FSRSIntegrationStats(
        learning_set_id=learning_set.id,
        dataset_id=learning_set.dataset_id,
        user_id=current_user.id,
        current_phase=current_phase,
        phase_description=phase_description,
        total_cards=total_cards,
        mastered_count=mastered_count,
        isolation_mastered_count=isolation_mastered_count,
        integration_confirmed_count=integration_confirmed_count,
        integration_review_count=integration_review_count,
        learning_count=learning_count,
        integration_efficiency=round(integration_efficiency, 1),
        first_attempt_success_rate=round(first_attempt_success_rate, 1),
        average_integration_attempts=round(average_integration_attempts, 1),
        reconsolidation_rate=round(reconsolidation_rate, 1),
        stability_stats=stability_stats,
        session_start_time=session_start_time,
        last_activity_time=last_activity_time,
        total_session_time_minutes=round(total_session_time_minutes, 1) if total_session_time_minutes else None,
        card_details=card_details
    )


# =============================================================================
# STATUS SYNCHRONIZATION ENDPOINTS - PHASE 1 IMPLEMENTATION
# =============================================================================

@router.post("/cards/{element_id}/fix-status")
def fix_card_status(
    element_id: str, 
    learning_set_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fix status inconsistency for a specific card - Phase 1.1 implementation
    
    Args:
        element_id: Element ID to fix
        learning_set_id: Optional learning set ID for context
        
    Returns:
        dict: Fix result including old/new status
    """
    from ..utils.status_sync import validate_and_sync_card_status
    
    result = validate_and_sync_card_status(db, element_id, current_user.id, learning_set_id)
    
    if result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fix card status: {result.get('message')}"
        )
    
    return result


@router.post("/learning-sets/{learning_set_id}/fix-all-status")
def fix_learning_set_status(
    learning_set_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fix status inconsistencies for all cards in learning set - Phase 1.1 batch implementation
    
    Args:
        learning_set_id: Learning set ID
        
    Returns:
        dict: Batch fix results
    """
    from ..utils.status_sync import batch_validate_learning_set
    
    # Verify user owns the learning set
    learning_set = db.query(UserLearningSet).filter(
        UserLearningSet.id == learning_set_id,
        UserLearningSet.user_id == current_user.id
    ).first()
    
    if not learning_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning set not found or access denied"
        )
    
    result = batch_validate_learning_set(db, learning_set_id, current_user.id)
    
    if result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fix learning set status: {result.get('message')}"
        )
    
    return result


@router.get("/system/config/validate")
def validate_system_config(db: Session = Depends(get_db)):
    """
    Validate system configuration - Phase 1.3 implementation
    
    Returns:
        dict: Configuration validation results
    """
    from ..utils.status_sync import validate_classification_config
    
    return validate_classification_config(db)


@router.get("/cards/{element_id}/debug")
def get_card_debug_info(
    element_id: str,
    learning_set_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get basic debug information for a card - Phase 2.1 implementation
    
    Args:
        element_id: Element ID to debug
        learning_set_id: Optional learning set ID for context
        
    Returns:
        dict: Debug information including status consistency and attempts analysis
    """
    
    # Get current data
    review = db.query(UserElementReview).filter(
        UserElementReview.user_id == current_user.id,
        UserElementReview.element_id == element_id
    ).first()
    
    attempts = db.query(UserFieldAttempt).filter(
        UserFieldAttempt.user_id == current_user.id,
        UserFieldAttempt.element_id == element_id
    ).order_by(UserFieldAttempt.attempted_at.desc()).all()
    
    # Get learning set if provided
    learning_set = None
    if learning_set_id:
        learning_set = db.query(UserLearningSet).filter(
            UserLearningSet.id == learning_set_id,
            UserLearningSet.user_id == current_user.id
        ).first()
    
    # Compute status
    computed_status = classify_card_status(db, review, attempts, learning_set)
    stored_status = review.status if review else None
    
    # Basic attempt analysis
    if attempts:
        total_attempts = len(attempts)
        correct_attempts = sum(1 for a in attempts if a.is_correct)
        accuracy = correct_attempts / total_attempts
        recent_attempts = attempts[-5:]  # Last 5 attempts
        
        # Success pattern analysis
        recent_pattern = [a.is_correct for a in recent_attempts]
        success_streak = 0
        for is_correct in reversed(recent_pattern):
            if is_correct:
                success_streak += 1
            else:
                break
    else:
        total_attempts = correct_attempts = accuracy = success_streak = 0
        recent_attempts = []
        recent_pattern = []
    
    # Check for common issues
    issues = []
    if stored_status != computed_status:
        issues.append({
            "type": "status_inconsistency",
            "message": f"Stored status '{stored_status}' doesn't match computed status '{computed_status}'"
        })
    
    if total_attempts > 10 and stored_status == "learning":
        issues.append({
            "type": "stuck_in_learning",
            "message": f"Card has {total_attempts} attempts but still in learning status"
        })
    
    if accuracy > 0.8 and total_attempts >= 3 and stored_status in ["learning", "new"]:
        issues.append({
            "type": "high_accuracy_not_progressing",
            "message": f"High accuracy ({accuracy:.1%}) but status hasn't advanced"
        })
    
    return {
        "element_id": element_id,
        "stored_status": stored_status,
        "computed_status": computed_status,
        "status_consistent": stored_status == computed_status,
        "attempts_summary": {
            "total": total_attempts,
            "correct": correct_attempts,
            "accuracy": accuracy,
            "success_streak": success_streak,
            "recent_pattern": recent_pattern
        },
        "timestamps": {
            "last_attempt": attempts[-1].attempted_at.isoformat() if attempts else None,
            "review_created": review.created_at.isoformat() if review else None,
            "review_updated": review.updated_at.isoformat() if review else None
        },
        "learning_context": {
            "learning_set_id": learning_set_id,
            "learning_set_phase": learning_set.isolation_phase if learning_set else None
        },
        "issues": issues,
        "debug_timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health/classification")
def classification_health_check(db: Session = Depends(get_db)):
    """
    Simple health check for classification system - Phase 4.1 implementation
    
    Returns:
        dict: System health information
    """
    
    try:
        # Test database connectivity
        from sqlalchemy import text
        db.execute(text("SELECT 1")).scalar()
        db_status = "connected"
        
        # Test configuration loading
        try:
            config = get_classification_config(db)
            config_status = "loaded" if config else "empty"
        except Exception:
            config_status = "error"
        
        # Quick consistency check (sample 10 cards)
        sample_reviews = db.query(UserElementReview).limit(10).all()
        inconsistent_count = 0
        sample_size = len(sample_reviews)
        
        for review in sample_reviews:
            try:
                attempts = db.query(UserFieldAttempt).filter(
                    UserFieldAttempt.user_id == review.user_id,
                    UserFieldAttempt.element_id == review.element_id
                ).order_by(UserFieldAttempt.attempted_at.desc()).all()
                
                computed_status = classify_card_status(db, review, attempts, None)
                if review.status != computed_status:
                    inconsistent_count += 1
            except Exception:
                # Count classification errors as inconsistencies
                inconsistent_count += 1
        
        consistency_rate = (sample_size - inconsistent_count) / sample_size if sample_size > 0 else 1.0
        
        # Overall health score
        health_score = 100
        if db_status != "connected": 
            health_score -= 50
        if config_status == "error": 
            health_score -= 30
        elif config_status == "empty": 
            health_score -= 15
        if consistency_rate < 0.9: 
            health_score -= 20
        if consistency_rate < 0.7:
            health_score -= 20  # Extra penalty for very low consistency
        
        # Determine overall status
        if health_score >= 80:
            overall_status = "healthy"
        elif health_score >= 50:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        # Get cache statistics if available
        try:
            from ..utils.simple_cache import get_cache_stats
            cache_stats = get_cache_stats()
        except Exception:
            cache_stats = {"error": "Cache stats unavailable"}
        
        return {
            "status": overall_status,
            "health_score": health_score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "database": db_status,
                "configuration": config_status,
                "consistency_rate": round(consistency_rate, 3),
                "sample_size": sample_size,
                "inconsistent_cards": inconsistent_count
            },
            "performance": {
                "cache_stats": cache_stats
            },
            "recommendations": _get_health_recommendations(health_score, db_status, config_status, consistency_rate)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "health_score": 0,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "database": "error",
                "configuration": "error",
                "consistency_rate": 0,
                "sample_size": 0
            }
        }


def _get_health_recommendations(health_score: int, db_status: str, config_status: str, consistency_rate: float) -> List[str]:
    """
    Get health improvement recommendations - Phase 4.1 helper
    
    Args:
        health_score: Overall health score
        db_status: Database status
        config_status: Configuration status
        consistency_rate: Status consistency rate
    
    Returns:
        List[str]: List of recommendations
    """
    recommendations = []
    
    if db_status != "connected":
        recommendations.append("Check database connectivity")
    
    if config_status == "error":
        recommendations.append("Fix configuration loading errors")
    elif config_status == "empty":
        recommendations.append("Review system configuration - some configs may be missing")
    
    if consistency_rate < 0.7:
        recommendations.append("Critical: Many cards have status inconsistencies - run batch status fix")
    elif consistency_rate < 0.9:
        recommendations.append("Warning: Some cards have status inconsistencies - consider running status validation")
    
    if health_score < 50:
        recommendations.append("System requires immediate attention")
    elif health_score < 80:
        recommendations.append("System performance is degraded - review issues above")
    
    if not recommendations:
        recommendations.append("System is operating normally")
    
    return recommendations


# New endpoint for detailed card statistics by learning set
@router.get("/learning-sets/{learning_set_id}/detailed-stats")
def get_detailed_card_stats(
    learning_set_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed statistics for each card in a learning set,
    showing attempt counts by status and correctness.
    """
    try:
        # Get the learning set and verify it belongs to the current user
        learning_set = db.query(UserLearningSet).filter(
            UserLearningSet.id == learning_set_id,
            UserLearningSet.user_id == current_user.id
        ).first()
        
        if not learning_set:
            raise HTTPException(
                status_code=404, 
                detail="Learning set not found or not accessible"
            )
        
        # Get all cards in the learning set
        learning_set_items = db.query(UserLearningSetItem).filter(
            UserLearningSetItem.learning_set_id == learning_set_id
        ).all()
        
        if not learning_set_items:
            raise HTTPException(
                status_code=404, 
                detail="No items found in learning set"
            )
        
        detailed_stats = []
        
        for item in learning_set_items:
            element_id = item.element_id
            
            # Get element details
            element = db.query(Element).filter(Element.id == element_id).first()
            if not element:
                continue
            
            # Get element fields to create a display string
            fields = db.query(Field).filter(Field.element_id == element_id).all()
            element_display = f"{element.code or 'Element'}"
            if fields:
                # Use the first field value as display content
                primary_field = fields[0]
                field_content = primary_field.field_value[:100] + '...' if len(primary_field.field_value) > 100 else primary_field.field_value
                element_display = f"{primary_field.field_name}: {field_content}"
                
            # Get current review status
            review = db.query(UserElementReview).filter(
                UserElementReview.user_id == current_user.id,
                UserElementReview.element_id == element_id
            ).first()
            
            # Get all attempts for this card
            all_attempts = db.query(UserFieldAttempt).filter(
                UserFieldAttempt.user_id == current_user.id,
                UserFieldAttempt.element_id == element_id
            ).order_by(UserFieldAttempt.attempted_at.asc()).all()
            
            # Calculate stats by status using proper phase tracking
            stats_by_status = {
                'learning': {'correct': 0, 'incorrect': 0, 'total': 0},
                'isolation_mastered': {'correct': 0, 'incorrect': 0, 'total': 0},
                'integration_review': {'correct': 0, 'incorrect': 0, 'total': 0},
                'integration_confirmed': {'correct': 0, 'incorrect': 0, 'total': 0},
                'spiral_review': {'correct': 0, 'incorrect': 0, 'total': 0}
            }
            
            # Use the last_integration_attempt timestamp to categorize attempts
            if all_attempts:
                integration_start_time = getattr(review, 'last_integration_attempt', None) if review else None
                
                for attempt in all_attempts:
                    # Determine the phase for this attempt
                    # Fix timezone comparison issue by ensuring both datetimes have the same timezone awareness
                    if integration_start_time and attempt.attempted_at:
                        # Make both datetimes timezone-aware for comparison
                        attempt_time = attempt.attempted_at
                        start_time = integration_start_time
                        
                        # If one is naive and the other is aware, make them compatible
                        if attempt_time.tzinfo is None and start_time.tzinfo is not None:
                            # Make attempt_time timezone-aware (assume UTC)
                            attempt_time = attempt_time.replace(tzinfo=timezone.utc)
                        elif attempt_time.tzinfo is not None and start_time.tzinfo is None:
                            # Make start_time timezone-aware (assume UTC)
                            start_time = start_time.replace(tzinfo=timezone.utc)
                        
                        if attempt_time >= start_time:
                            # This attempt was made in integration phase
                            # For now, classify all integration attempts as integration_review
                            # (in a more sophisticated version, we'd track exact status transitions)
                            phase = 'integration_review'
                        else:
                            # This attempt was made in isolation phase
                            # Use simple heuristic based on attempt sequence
                            attempts_before_this = [a for a in all_attempts if a.attempted_at < attempt.attempted_at]
                            if len(attempts_before_this) < 3:
                                phase = 'learning'
                            else:
                                # Check if the attempts before this were generally successful
                                correct_before = sum(1 for a in attempts_before_this if a.is_correct)
                                accuracy_before = correct_before / len(attempts_before_this)
                                if accuracy_before >= 0.8:
                                    phase = 'isolation_mastered'
                                else:
                                    phase = 'learning'
                    else:
                        # No integration start time or attempt time - assume isolation phase
                        # Use simple heuristic based on attempt sequence
                        attempts_before_this = [a for a in all_attempts if a.attempted_at < attempt.attempted_at]
                        if len(attempts_before_this) < 3:
                            phase = 'learning'
                        else:
                            # Check if the attempts before this were generally successful
                            correct_before = sum(1 for a in attempts_before_this if a.is_correct)
                            accuracy_before = correct_before / len(attempts_before_this)
                            if accuracy_before >= 0.8:
                                phase = 'isolation_mastered'
                            else:
                                phase = 'learning'
                    
                    # Count the attempt in the appropriate phase
                    if attempt.is_correct:
                        stats_by_status[phase]['correct'] += 1
                    else:
                        stats_by_status[phase]['incorrect'] += 1
                    stats_by_status[phase]['total'] += 1
            
            # Calculate overall stats
            total_attempts = len(all_attempts)
            total_correct = sum(1 for a in all_attempts if a.is_correct)
            overall_accuracy = (total_correct / total_attempts) if total_attempts > 0 else 0
            
            # Get the current computed status
            current_status = review.status if review else 'not_started'
            
            detailed_stats.append({
                'element_id': element_id,
                'element_content': element_display,
                'current_status': current_status,
                'total_attempts': total_attempts,
                'total_correct': total_correct,
                'overall_accuracy': round(overall_accuracy, 3),
                'stats_by_status': stats_by_status,
                'last_attempt': all_attempts[-1].attempted_at.isoformat() if all_attempts else None,
                'created_at': item.added_at.isoformat()
            })
        
        # Sort by total attempts (most practiced first)
        detailed_stats.sort(key=lambda x: x['total_attempts'], reverse=True)
        
        # Calculate summary statistics
        total_cards = len(detailed_stats)
        cards_with_attempts = sum(1 for card in detailed_stats if card['total_attempts'] > 0)
        average_attempts_per_card = sum(card['total_attempts'] for card in detailed_stats) / total_cards if total_cards > 0 else 0
        
        # Status distribution
        status_distribution = {}
        for card in detailed_stats:
            status = card['current_status']
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        return {
            'learning_set_id': learning_set_id,
            'summary': {
                'total_cards': total_cards,
                'cards_with_attempts': cards_with_attempts,
                'average_attempts_per_card': round(average_attempts_per_card, 2),
                'status_distribution': status_distribution
            },
            'cards': detailed_stats,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in get_detailed_card_stats: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get detailed card stats: {str(e)}"
        )


@router.post("/learning-sets/{learning_set_id}/fix-integration-status")
async def fix_integration_status(
    learning_set_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fix cards that are incorrectly marked as integration_confirmed without proper integration attempts.
    This resets such cards to integration_review status.
    """
    try:
        # Verify learning set belongs to user
        learning_set = db.query(UserLearningSet).filter(
            and_(
                UserLearningSet.id == learning_set_id,
                UserLearningSet.user_id == current_user.id
            )
        ).first()
        
        if not learning_set:
            raise HTTPException(
                status_code=404, 
                detail="Learning set not found or not accessible"
            )
        
        # Get all cards in this learning set that are marked as integration_confirmed
        learning_set_items = db.query(UserLearningSetItem).filter(
            UserLearningSetItem.learning_set_id == learning_set_id
        ).all()
        
        element_ids = [item.element_id for item in learning_set_items]
        
        # Find reviews that are integration_confirmed but have no integration attempts
        problematic_reviews = db.query(UserElementReview).filter(
            and_(
                UserElementReview.user_id == current_user.id,
                UserElementReview.element_id.in_(element_ids),
                UserElementReview.status == "integration_confirmed",
                or_(
                    UserElementReview.last_integration_attempt.is_(None),
                    UserElementReview.integration_attempts == 0
                )
            )
        ).all()
        
        fixed_count = 0
        for review in problematic_reviews:
            # Check if this card actually has any attempts made during integration phase
            if review.last_integration_attempt:
                # Get attempts made after integration start
                integration_attempts = db.query(UserFieldAttempt).filter(
                    and_(
                        UserFieldAttempt.user_id == current_user.id,
                        UserFieldAttempt.element_id == review.element_id,
                        UserFieldAttempt.attempted_at >= review.last_integration_attempt
                    )
                ).count()
                
                if integration_attempts == 0:
                    # No integration attempts but marked as integration_confirmed - fix it
                    review.status = "integration_review"
                    review.integration_confirmed = False
                    review.last_integration_attempt = None  # Reset timestamp
                    fixed_count += 1
            else:
                # No integration timestamp at all - definitely needs fixing
                review.status = "integration_review" 
                review.integration_confirmed = False
                fixed_count += 1
        
        db.commit()
        
        return {
            "message": f"Fixed {fixed_count} cards that were incorrectly marked as integration_confirmed",
            "fixed_count": fixed_count,
            "total_checked": len(problematic_reviews)
        }
        
    except Exception as e:
        db.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in fix_integration_status: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fix integration status: {str(e)}"
        )
