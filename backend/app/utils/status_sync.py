"""
Status Synchronization and Validation System
Implements Phase 1 of the simplified incremental improvement plan
"""

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

from ..sessions.models import UserElementReview, UserFieldAttempt, UserLearningSet, UserLearningSetItem
from ..sessions.routes import classify_card_status

# Set up classification logger
classification_logger = logging.getLogger("flashcard.classification")
classification_logger.setLevel(logging.INFO)

def validate_and_sync_card_status(db: Session, element_id: str, user_id: str, learning_set_id: str = None) -> dict:
    """
    Simple status validation and sync - Phase 1.1 implementation
    
    Args:
        db: Database session
        element_id: Element to validate
        user_id: User ID
        learning_set_id: Learning set ID (optional, for learning set context)
    
    Returns:
        dict: Validation and sync results
    """
    try:
        # Get current data
        review = db.query(UserElementReview).filter(
            UserElementReview.user_id == user_id,
            UserElementReview.element_id == element_id
        ).first()
        
        attempts = db.query(UserFieldAttempt).filter(
            UserFieldAttempt.user_id == user_id,
            UserFieldAttempt.element_id == element_id
        ).order_by(UserFieldAttempt.attempted_at.desc()).all()
        
        # Get learning set if provided
        learning_set = None
        if learning_set_id:
            learning_set = db.query(UserLearningSet).filter(
                UserLearningSet.id == learning_set_id
            ).first()
        
        # Compute what status should be
        computed_status = classify_card_status(db, review, attempts, learning_set)
        stored_status = review.status if review else None
        
        # Check consistency
        if stored_status != computed_status:
            # Auto-fix: Update stored status to match computed
            if review:
                old_status = review.status
                review.status = computed_status
                review.updated_at = datetime.now(timezone.utc)
            else:
                # Create new review with computed status
                review = UserElementReview(
                    user_id=user_id,
                    element_id=element_id,
                    status=computed_status,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    accuracy_percentage=0.0,
                    stability_score=1.0
                )
                db.add(review)
                old_status = None
            
            db.commit()
            
            # Log the fix
            classification_logger.info(
                f"Status sync fix applied: {element_id}",
                extra={
                    "element_id": element_id,
                    "user_id": user_id,
                    "old_status": old_status,
                    "new_status": computed_status,
                    "attempts_count": len(attempts) if attempts else 0
                }
            )
            
            return {
                "fixed": True,
                "old_status": old_status,
                "new_status": computed_status,
                "element_id": element_id,
                "attempts_analyzed": len(attempts) if attempts else 0
            }
        
        return {
            "fixed": False, 
            "status": stored_status, 
            "element_id": element_id,
            "attempts_analyzed": len(attempts) if attempts else 0
        }
        
    except Exception as e:
        classification_logger.error(
            f"Status validation failed: {element_id}",
            extra={
                "element_id": element_id,
                "user_id": user_id,
                "error": str(e)
            }
        )
        return {
            "error": True,
            "message": str(e),
            "element_id": element_id
        }


def validate_classification_config(db: Session) -> dict:
    """
    Basic validation of classification configuration - Phase 1.3 implementation
    
    Args:
        db: Database session
    
    Returns:
        dict: Configuration validation results
    """
    try:
        from app.sessions.routes import get_classification_config
        config = get_classification_config(db)
        warnings = []
        
        # Check critical thresholds
        critical_configs = [
            "learning_accuracy_threshold",
            "learning_min_attempts", 
            "integration_accuracy_threshold",
            "spiral_interval_hours"
        ]
        
        for config_name in critical_configs:
            if config_name not in config:
                warnings.append(f"Missing configuration: {config_name}")
            elif config[config_name] is None:
                warnings.append(f"Null configuration: {config_name}")
        
        # Basic range checks
        if config.get("learning_accuracy_threshold", 0) > 1.0:
            warnings.append("learning_accuracy_threshold should be <= 1.0")
        
        if config.get("learning_min_attempts", 0) < 1:
            warnings.append("learning_min_attempts should be >= 1")
            
        if config.get("integration_accuracy_threshold", 0) > 1.0:
            warnings.append("integration_accuracy_threshold should be <= 1.0")
            
        if config.get("spiral_interval_hours", 0) < 1:
            warnings.append("spiral_interval_hours should be >= 1")
        
        return {
            "config_valid": len(warnings) == 0,
            "warnings": warnings,
            "total_configs": len(config),
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "config_valid": False,
            "warnings": [f"Configuration loading failed: {str(e)}"],
            "total_configs": 0,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }


def classify_card_status_with_logging(db: Session, review, attempts, learning_set):
    """
    Wrapper around existing classify_card_status with enhanced logging - Phase 1.2 implementation
    
    Args:
        db: Database session
        review: UserElementReview instance
        attempts: List of UserFieldAttempt instances
        learning_set: UserLearningSet instance
    
    Returns:
        str: Card status
    """
    element_id = review.element_id if review else "unknown"
    
    try:
        # Call existing classification logic
        status = classify_card_status(db, review, attempts, learning_set)
        
        # Log successful classification
        classification_logger.info(
            f"Card classification successful: {element_id} -> {status}",
            extra={
                "element_id": element_id,
                "status": status,
                "attempts_count": len(attempts) if attempts else 0,
                "accuracy": sum(1 for a in attempts if a.is_correct) / len(attempts) if attempts else 0,
                "learning_set_id": learning_set.id if learning_set else None
            }
        )
        
        return status
        
    except Exception as e:
        # Log classification errors
        classification_logger.error(
            f"Card classification failed: {element_id}",
            extra={
                "element_id": element_id,
                "error": str(e),
                "attempts_count": len(attempts) if attempts else 0,
                "learning_set_id": learning_set.id if learning_set else None
            }
        )
        
        # Return fallback status
        return review.status if review and review.status else "learning"


def batch_validate_learning_set(db: Session, learning_set_id: str, user_id: str) -> dict:
    """
    Fix status inconsistencies for all cards in learning set - Phase 1.1 batch operation
    
    Args:
        db: Database session
        learning_set_id: Learning set ID
        user_id: User ID
    
    Returns:
        dict: Batch validation results
    """
    try:
        # Get all items in learning set
        items = db.query(UserLearningSetItem).filter(
            UserLearningSetItem.learning_set_id == learning_set_id
        ).all()
        
        fixed_count = 0
        results = []
        errors = []
        
        for item in items:
            result = validate_and_sync_card_status(db, item.element_id, user_id, learning_set_id)
            
            if result.get("error"):
                errors.append(result)
            elif result.get("fixed"):
                fixed_count += 1
                
            results.append(result)
        
        return {
            "learning_set_id": learning_set_id,
            "total_cards": len(items),
            "fixed_count": fixed_count,
            "error_count": len(errors),
            "results": results,
            "errors": errors,
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        classification_logger.error(
            f"Batch validation failed: {learning_set_id}",
            extra={
                "learning_set_id": learning_set_id,
                "user_id": user_id,
                "error": str(e)
            }
        )
        
        return {
            "error": True,
            "message": str(e),
            "learning_set_id": learning_set_id,
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
