"""
Session Routes

FastAPI routes for managing learning sessions and flashcard interactions.
"""
from datetime import datetime, timedelta, timezone
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
from ..auth.routes import get_current_user
from ..auth.models import User
from ..datasets.models import Dataset, Element, Field
from ..database import get_db
from ..admin.models import SystemConfig

# Import the progress update function
from ..dashboard.routes import _update_dataset_progress

router = APIRouter(prefix="/sessions", tags=["learning-sessions"])

# Default configuration constants (fallbacks)
DEFAULT_INITIAL_SET_SIZE = 10
DEFAULT_STAGE_INCREMENT = 10
DEFAULT_MASTERY_THRESHOLD = 3
DEFAULT_MAX_SET_SIZE = 30  # Changed from 50 to 30
DEFAULT_MID_TIER_THRESHOLD = 80  # Threshold for mid-tier optimization (16-80 cards)
DEFAULT_DISTRACTOR_COUNT = 3  # Number of wrong answer choices to generate

# Temporary in-memory storage for timer settings (until we add DB fields)
# In production, this would be stored in Redis or the database
timer_settings_cache = {}


def get_learning_config(db: Session):
    """Get current learning configuration from database or defaults"""
    return {
        'initial_set_size': SystemConfig.get_value(db, "initial_set_size", DEFAULT_INITIAL_SET_SIZE),
        'stage_increment': SystemConfig.get_value(db, "stage_increment", DEFAULT_STAGE_INCREMENT),
        'mastery_threshold': SystemConfig.get_value(db, "mastery_threshold", DEFAULT_MASTERY_THRESHOLD),
        'max_set_size': SystemConfig.get_value(db, "max_set_size", DEFAULT_MAX_SET_SIZE),
        'mid_tier_threshold': SystemConfig.get_value(db, "mid_tier_threshold", DEFAULT_MID_TIER_THRESHOLD),
        'chunk_size_progression': SystemConfig.get_value(db, "chunk_size_progression", "100,75,60,50"),
        'reinforcement_percentage': SystemConfig.get_value(db, "reinforcement_percentage", 10),
        'distractor_count': SystemConfig.get_value(db, "distractor_count", DEFAULT_DISTRACTOR_COUNT),
    }


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
            UserElementReview.status == "mastered",
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
            UserElementReview.status == "mastered"
        )
    ).join(Element).filter(Element.dataset_id == current_learning_set.dataset_id).subquery()
    
    # Get new elements for next chunk
    new_elements = db.query(Element).filter(
        and_(
            Element.dataset_id == current_learning_set.dataset_id,
            ~Element.id.in_(mastered_element_ids)
        )
    ).limit(next_chunk_size).all()
    
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
        
        # Get optimal learning parameters based on dataset size
        optimal_params = get_optimal_learning_parameters(total_elements, config)
        
        # Determine session parameters
        if request.force_review:
            # For force review, include ALL elements in one session
            chunk_number = 1
            total_chunks = 1
            current_chunk_size = total_elements
            learning_message = f"Force review mode: All {total_elements} cards will be reviewed."
        elif optimal_params['is_chunked']:
            # Chunked learning for large datasets
            chunk_number = 1
            total_chunks = calculate_total_chunks(total_elements, config['chunk_size_progression'])
            current_chunk_size = get_adaptive_chunk_size(chunk_number, config['chunk_size_progression'])
            learning_message = optimal_params['message']
        else:
            # Regular or optimized progressive learning
            chunk_number = None
            total_chunks = None
            current_chunk_size = optimal_params['initial_set_size']
            learning_message = optimal_params['message']
        
        # Create new learning set
        learning_set = UserLearningSet(
            user_id=current_user.id,
            dataset_id=request.dataset_id,
            stage=1,
            status="active",
            mode=request.mode or "progressive",
            chunk_number=chunk_number,
            total_chunks=total_chunks,
            chunk_size=current_chunk_size,
            total_dataset_size=total_elements
        )
        db.add(learning_set)
        db.flush()
        
        # Select elements for this chunk
        if request.force_review:
            # For force review, include ALL elements in the dataset
            elements = db.query(Element).filter(Element.dataset_id == request.dataset_id).all()
        elif chunk_number:
            # Chunked learning: skip already mastered elements and get new ones
            mastered_element_ids = db.query(UserElementReview.element_id).filter(
                and_(
                    UserElementReview.user_id == current_user.id,
                    UserElementReview.status == "mastered"
                )
            ).join(Element).filter(Element.dataset_id == request.dataset_id).subquery()
            
            # Get new elements (not yet mastered)
            new_elements = db.query(Element).filter(
                and_(
                    Element.dataset_id == request.dataset_id,
                    ~Element.id.in_(mastered_element_ids)
                )
            ).limit(current_chunk_size).all()
            
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
            # Regular progressive learning
            elements = db.query(Element).filter(Element.dataset_id == request.dataset_id).limit(current_chunk_size).all()
        
        # Add elements to the learning set
        for i, element in enumerate(elements):
            item = UserLearningSetItem(
                learning_set_id=learning_set.id,
                element_id=element.id,
                position=i + 1
            )
            db.add(item)
        
        db.commit()
        db.refresh(learning_set)
    
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
        )
    
    # Get elements in the learning set
    element_ids = [item.element_id for item in learning_set.items]
    
    # Priority 1: Due items (spaced repetition)
    due_reviews = db.query(UserElementReview).filter(
        and_(
            UserElementReview.user_id == current_user.id,
            UserElementReview.element_id.in_(element_ids),
            UserElementReview.next_due <= datetime.utcnow(),
            UserElementReview.status != "mastered"
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
            element_id = random.choice(new_element_ids)
        else:
            # Check if all elements are mastered
            mastered_count = db.query(func.count(UserElementReview.id)).filter(
                and_(
                    UserElementReview.user_id == current_user.id,
                    UserElementReview.element_id.in_(element_ids),
                    UserElementReview.status == "mastered"
                )
            ).scalar() or 0
            
            # If all elements are mastered and not forcing review, check for chunk completion
            if mastered_count >= len(element_ids) and not force_review:
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
                    # Progressive learning - check if we can advance to next stage
                    config = get_learning_config(db)
                    stage_increment = get_stage_increment_for_learning_set(learning_set, config)
                    
                    # Check if there are more elements available in the dataset
                    current_element_ids = [item.element_id for item in learning_set.items]
                    total_dataset_elements = db.query(func.count(Element.id)).filter(
                        Element.dataset_id == learning_set.dataset_id
                    ).scalar() or 0
                    
                    if len(current_element_ids) < total_dataset_elements and stage_increment > 0:
                        # Auto-advance to next stage by adding more elements
                        new_elements = db.query(Element).filter(
                            and_(
                                Element.dataset_id == learning_set.dataset_id,
                                ~Element.id.in_(current_element_ids)
                            )
                        ).limit(stage_increment).all()
                        
                        # Add new elements to the learning set
                        for element in new_elements:
                            item = UserLearningSetItem(
                                learning_set_id=learning_set.id,
                                element_id=element.id,
                                position=len(learning_set.items) + 1
                            )
                            db.add(item)
                        
                        # Update stage and commit
                        learning_set.stage += 1
                        learning_set.updated_at = datetime.utcnow()
                        db.commit()
                        
                        # Refresh the learning set to get the updated items relationship
                        db.refresh(learning_set)
                        
                        # After adding elements, get the updated element_ids for card selection
                        element_ids = [item.element_id for item in learning_set.items]
                        
                        # Now select from the newly added elements (they will be new/unreviewed)
                        reviewed_element_ids = db.query(UserElementReview.element_id).filter(
                            and_(
                                UserElementReview.user_id == current_user.id,
                                UserElementReview.element_id.in_(element_ids)
                            )
                        ).all()
                        reviewed_ids = [r[0] for r in reviewed_element_ids]
                        
                        new_element_ids = [eid for eid in element_ids if eid not in reviewed_ids]
                        
                        if new_element_ids:
                            element_id = random.choice(new_element_ids)
                        else:
                            # This shouldn't happen, but fallback to any element
                            element_id = random.choice(element_ids)
                    else:
                        # No more elements or no stage increment - complete session
                        learning_set.status = "completed"
                        db.commit()
                        
                        # Update dataset progress
                        await _update_dataset_progress(db, current_user.id)
                        
                        raise HTTPException(
                            status_code=status.HTTP_204_NO_CONTENT,
                            detail="Session complete - all elements mastered"
                        )
            
            # Priority 3: Any item in the set (if forcing review, include mastered items)
            if force_review:
                # Include all items, even mastered ones
                all_reviews = db.query(UserElementReview).filter(
                    and_(
                        UserElementReview.user_id == current_user.id,
                        UserElementReview.element_id.in_(element_ids)
                    )
                ).all()
                
                if all_reviews:
                    element_id = random.choice([r.element_id for r in all_reviews])
                else:
                    # If no reviews exist, pick any element from the set
                    element_id = random.choice(element_ids)
            else:
                # Priority 3: Any item in the set (not mastered)
                non_mastered_reviews = db.query(UserElementReview).filter(
                    and_(
                        UserElementReview.user_id == current_user.id,
                        UserElementReview.element_id.in_(element_ids),
                        UserElementReview.status != "mastered"
                    )
                ).all()
                
                if non_mastered_reviews:
                    element_id = random.choice([r.element_id for r in non_mastered_reviews])
                else:
                    # Fallback to any element
                    element_id = random.choice(element_ids)
    
    # Get the element and its fields
    element = db.query(Element).filter(Element.id == element_id).first()
    if not element:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Element not found"
        )
    
    # Get all fields for this element
    fields = db.query(Field).filter(Field.element_id == element_id).all()
    if len(fields) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Element must have at least 2 fields for flashcard creation"
        )
    
    # Select question and answer fields
    field_names = [f.field_name for f in fields]
    question_field_name = random.choice(field_names)
    answer_field_name = random.choice([f for f in field_names if f != question_field_name])
    
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
    
    # Generate distractors (wrong answers) from other elements in the current learning set
    # Join directly with the learning set items table to ensure distractors come from current set
    distractor_fields = db.query(Field).join(
        UserLearningSetItem,
        Field.element_id == UserLearningSetItem.element_id
    ).filter(
        and_(
            UserLearningSetItem.learning_set_id == learning_set.id,
            Field.field_name == answer_field_name,
            Field.element_id != element_id
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
        timer_mode=timer_settings['timer_mode']
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
    
    # Get current learning configuration
    config = get_learning_config(db)
    
    # Update review based on answer
    review.review_count += 1
    review.last_reviewed = datetime.utcnow()

    if request.is_correct:
        review.success_streak += 1
        
        # Spaced repetition algorithm - modified for force review
        mastery_threshold = 1 if is_force_review else config['mastery_threshold']
        
        if review.success_streak >= mastery_threshold:
            review.status = "mastered"
            review.interval_days = min(review.interval_days * 2, 365)  # Cap at 1 year
        else:
            review.status = "learning"
            review.interval_days = review.success_streak  # 1, 2, 3 days
        
        # Adjust ease factor slightly up
        review.ease_factor = min(review.ease_factor + 5, 300)  # Cap at 3.0
    else:
        # Reset on failure
        review.success_streak = 0
        review.status = "learning"
        review.interval_days = 1
        review.is_difficult = True
        
        # Adjust ease factor down
        review.ease_factor = max(review.ease_factor - 20, 130)  # Floor at 1.3
    
    # Calculate next due date
    ease = review.ease_factor / 100.0
    review.next_due = datetime.utcnow() + timedelta(days=review.interval_days * ease)
    review.updated_at = datetime.utcnow()
    
    # Check if force review session is complete and reset mode
    if is_force_review and review.status == "mastered":
        element_ids = [item.element_id for item in learning_set.items]
        mastered_count = db.query(func.count(UserElementReview.id)).filter(
            and_(
                UserElementReview.user_id == current_user.id,
                UserElementReview.element_id.in_(element_ids),
                UserElementReview.status == "mastered"
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
    
    # Update dataset progress if element was mastered
    if review.status == "mastered":
        await _update_dataset_progress(db, current_user.id)
    
    # Create explanation with timer feedback
    explanation = f"Streak: {review.success_streak}, Next review in {review.interval_days} days"
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
    
    element_ids = [item.element_id for item in learning_set.items]
    
    # Get review statistics
    reviews = db.query(UserElementReview).filter(
        and_(
            UserElementReview.user_id == current_user.id,
            UserElementReview.element_id.in_(element_ids)
        )
    ).all()
    
    # Calculate basic progress counts
    mastered_count = len([r for r in reviews if r.status == "mastered"])
    due_count = len([r for r in reviews if r.next_due and r.next_due <= datetime.now(timezone.utc)])
    new_count = len(element_ids) - len(reviews)
    
    # Calculate confidence categories for enhanced progress display
    strong_cards = [r for r in reviews if r.status == "mastered"]
    weak_cards = [r for r in reviews if r.status in ["learning", "due"] or r.is_difficult]
    new_cards_count = len(element_ids) - len(reviews)
    
    # Determine learning phase based on mastery progress
    total_cards = len(element_ids)
    strong_percentage = len(strong_cards) / total_cards * 100 if total_cards > 0 else 0
    
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
    
    # Get the appropriate stage increment for this learning set
    stage_increment = get_stage_increment_for_learning_set(learning_set, config)
    
    # Check if ready for next stage
    ready_for_next_stage = (
        learning_set.mode == "progressive" and
        mastered_count == len(element_ids) and
        stage_increment > 0 and  # Only progress if increment is > 0
        learning_set.stage * stage_increment < config['max_set_size']
    )
    
    return ProgressResponse(
        stage=learning_set.stage,
        total_items=len(element_ids),
        mastered_count=mastered_count,
        due_count=due_count,
        new_count=new_count,
        ready_for_next_stage=ready_for_next_stage,
        # Enhanced confidence-based fields
        strong_count=len(strong_cards),
        weak_count=len(weak_cards),
        question_count=0,  # Will be set by frontend session tracking
        learning_phase=learning_phase
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
    ).limit(stage_increment).all()
    
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
    strong_cards = [r for r in reviews if r.status == "mastered"]
    weak_cards = [r for r in reviews if r.status in ["learning", "due"] or r.is_difficult]
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
