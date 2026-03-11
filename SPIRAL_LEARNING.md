# Spiral Learning Implementation Guide

## Overview
Spiral learning enhances our batch-based learning system by adding comprehensive review cycles that reinforce previously learned material while introducing new content. This prevents the forgetting curve and creates long-term retention through strategic revisiting of weak points.

## Current Learning Flow
```
Batch 1 (1-5) → Isolation
Batch 2 (6-10) → Isolation → Integration (1-10)
Batch 3 (11-15) → Isolation  
Batch 4 (16-20) → Isolation → Integration (11-20)
```

## Enhanced Spiral Learning Flow
```
Batch 1 (1-5) → Isolation
Batch 2 (6-10) → Isolation → Integration (1-10)
Batch 3 (11-15) → Isolation
Batch 4 (16-20) → Isolation → Integration (11-20)
TRIGGER: Spiral Review Session (1-20) - Focus on weak cards
Batch 5 (21-25) → Isolation
Batch 6 (26-30) → Isolation → Integration (21-30)
TRIGGER: Spiral Review Session (1-30) - Focus on weak cards
```

## Step-by-Step Implementation

### Phase 1: Database Enhancements ✅ COMPLETED

#### ✅ 1.1 Added Spiral Learning Fields to UserLearningSet
**File:** `backend/app/sessions/models.py`

Added new fields to track spiral learning state:
```python
# Spiral learning tracking fields
completed_integration_cycles = Column(Integer, default=0)      # Count of completed integration cycles
spiral_review_mode = Column(Boolean, default=False)           # Currently in spiral review session
last_spiral_review = Column(DateTime(timezone=True))          # Timestamp of last spiral review
```

#### ✅ 1.2 Created and Applied Database Migration
**Files:** 
- `backend/migrations/spiral_learning.sql` - Direct SQL migration
- `backend/migrations/spiral_learning_migration.py` - Alembic migration

**Migration Applied:** ✅ COMPLETED
```sql
ALTER TABLE user_learning_sets 
ADD COLUMN IF NOT EXISTS completed_integration_cycles INTEGER DEFAULT 0;

ALTER TABLE user_learning_sets 
ADD COLUMN IF NOT EXISTS spiral_review_mode BOOLEAN DEFAULT FALSE;

ALTER TABLE user_learning_sets 
ADD COLUMN IF NOT EXISTS last_spiral_review TIMESTAMP WITH TIME ZONE;
```

**Verification:** ✅ All columns added successfully with proper data types and defaults
- `completed_integration_cycles` (integer, default: 0)
- `spiral_review_mode` (boolean, default: false)  
- `last_spiral_review` (timestamp with time zone, nullable)

**Backend Restart:** ✅ Backend successfully restarted and recognized new schema

**Fix Applied:** ✅ Corrected session start logic that was causing 500 Internal Server Error
- Removed duplicate learning set creation code that was interfering with session startup
- Moved spiral review messaging to correct location after learning set commit
- Fixed `AttributeError: 'NoneType' object has no attribute 'id'` error

**Additional Fix:** ✅ Resolved UnboundLocalError in get_next_flashcard function
- Fixed `UnboundLocalError: cannot access local variable 'mastered_count'` in sessions/next endpoint
- Initialized `mastered_count` variable early to prevent scoping issues
- Added proper early exit logic for spiral review mode card selection
```python
class UserLearningSet(Base):
    # ... existing fields ...
    
    # Spiral learning tracking
    completed_integration_cycles = Column(Integer, default=0)
    last_spiral_review_position = Column(Integer, default=0)
    is_spiral_review = Column(Boolean, default=False)
    spiral_review_source_range = Column(String(50))  # "1-20", "1-30", etc.
```

### Phase 2: Spiral Learning Logic

#### 2.1 Create Spiral Review Detection Function
**File:** `backend/app/sessions/routes.py`

```python
### Phase 2: Core Logic Implementation ✅ COMPLETED

#### ✅ 2.1 Implemented Spiral Review Trigger Function
**File:** `backend/app/sessions/routes.py`

```python
def should_trigger_spiral_review(db: Session, user_id: str, dataset_id: str, end_position: int, config: dict) -> tuple[bool, str]:
    """Check if spiral review should be triggered after integration completion."""
    spiral_enabled = config.get('spiral_learning_enabled', True)
    trigger_interval = config.get('spiral_review_trigger_interval', 2)
    
    if not spiral_enabled:
        return False, ""
    
    # Get current learning set and check integration cycle count
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
```

#### ✅ 2.2 Implemented Weak Cards Selection Function
**File:** `backend/app/sessions/routes.py`

```python
def get_spiral_review_cards(db: Session, user_id: str, dataset_id: str, end_position: int, config: dict) -> List:
    """Identify cards that need spiral review based on weakness indicators."""
    weakness_threshold = config.get('spiral_weakness_threshold', 0.6)
    stability_threshold = config.get('spiral_stability_threshold', 1.5)
    integration_failure_weight = config.get('spiral_integration_failure_weight', 2.0)
    max_cards = config.get('spiral_review_max_cards', 20)
    
    # Query for cards with performance data
    elements_with_reviews = db.query(
        Element, UserElementReview.accuracy_percentage, UserElementReview.stability_score,
        UserElementReview.integration_attempts, UserElementReview.review_count
    ).join(UserElementReview).join(UserLearningSetItem).join(UserLearningSet).filter(
        and_(
            Element.dataset_id == dataset_id,
            UserElementReview.user_id == user_id,
            UserLearningSet.dataset_id == dataset_id,
            UserLearningSetItem.position <= end_position,
            UserElementReview.review_count > 0
        )
    ).all()
    
    # Calculate weakness scores using multi-criteria algorithm
    weakness_scores = []
    for element, accuracy, stability, integration_attempts, review_count in elements_with_reviews:
        accuracy_score = max(0, weakness_threshold - (accuracy or 0.0))
        stability_score = max(0, stability_threshold - (stability or 1.0))
        integration_penalty = (integration_attempts or 0) * integration_failure_weight
        recency_bonus = 1.0 if (review_count or 0) < 3 else 0.5
        
        total_weakness = accuracy_score + stability_score + integration_penalty + recency_bonus
        if total_weakness > 0:
            weakness_scores.append((element, total_weakness))
    
    # Sort by weakness (highest first) and limit
    weakness_scores.sort(key=lambda x: x[1], reverse=True)
    return [element for element, score in weakness_scores[:max_cards]]
```
```

#### 2.2 Create Weak Cards Identification Function
**File:** `backend/app/sessions/routes.py`

```python
def get_spiral_review_cards(db: Session, user_id: str, dataset_id: str, end_position: int, config: dict) -> List[Element]:
    """
    Identify cards that need spiral review based on weakness indicators.
    """
    weakness_threshold = config.get('spiral_weakness_threshold', 0.6)
    stability_threshold = config.get('spiral_stability_threshold', 1.5)
    integration_failure_weight = config.get('spiral_integration_failure_weight', 2.0)
    max_cards = config.get('spiral_review_max_cards', 20)
    
    # Query for weak cards based on multiple criteria
    weak_cards_query = db.query(
        Element,
        UserElementReview.accuracy_percentage,
        UserElementReview.stability_score,
        UserElementReview.integration_attempts,
        UserElementReview.review_count
    ).join(
        UserElementReview, Element.id == UserElementReview.element_id
    ).filter(
        and_(
            Element.dataset_id == dataset_id,
            UserElementReview.user_id == user_id,
            # Include cards from positions 1 to end_position
            Element.id.in_(
                db.query(UserLearningSetItem.element_id).join(UserLearningSet).filter(
                    and_(
                        UserLearningSet.dataset_id == dataset_id,
                        UserLearningSetItem.position <= end_position
                    )
                )
            )
        )
    ).filter(
        or_(
            # Low accuracy cards
            UserElementReview.accuracy_percentage < weakness_threshold,
            # Low stability cards
            UserElementReview.stability_score < stability_threshold,
            # Cards with integration failures
            UserElementReview.integration_attempts > 0,
            # Cards that failed recently (last 7 days)
            and_(
                UserElementReview.last_reviewed >= datetime.utcnow() - timedelta(days=7),
                UserElementReview.accuracy_percentage < 0.8
            )
        )
    )
    
    # Calculate weakness score and sort by priority
    weakness_scores = []
    for element, accuracy, stability, integration_attempts, review_count in weak_cards_query.all():
        # Calculate composite weakness score
        accuracy_score = max(0, weakness_threshold - (accuracy or 0)) * 2
        stability_score = max(0, stability_threshold - (stability or 1.0))
        integration_penalty = integration_attempts * integration_failure_weight
        recency_bonus = 1.0 if review_count < 3 else 0.5  # Newer cards get priority
        
        total_weakness = accuracy_score + stability_score + integration_penalty + recency_bonus
        weakness_scores.append((element, total_weakness))
    
    # Sort by weakness score (highest first) and limit
    weakness_scores.sort(key=lambda x: x[1], reverse=True)
    return [element for element, score in weakness_scores[:max_cards]]
```

### Phase 3: Integration with Existing Flow ✅ COMPLETED

#### ✅ 3.1 Modified Integration Completion Logic
**File:** `backend/app/sessions/routes.py` (around line 1090)

Enhanced the integration completion section to check for spiral review triggers:
```python
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
        spiral_cards = get_spiral_review_cards(
            db, current_user.id, learning_set.dataset_id,
            learning_set.current_batch_end, config
        )
        
        if spiral_cards:
            # Enter spiral review mode
            learning_set.spiral_review_mode = True
            learning_set.last_spiral_review = datetime.utcnow()
            db.commit()
            db.refresh(learning_set)
            
            # Select a random card from spiral review set
            element_id = random.choice([card.id for card in spiral_cards])
            print(f"DEBUG: Triggered spiral review for {review_range}, selected card {element_id}")
        else:
            # No weak cards found, proceed to next batch normally
            should_spiral = False
    
    if not should_spiral:
        # Continue with normal batch progression logic
        # ... existing next batch logic ...
```

#### ✅ 3.2 Added Spiral Review Card Selection Priority
**File:** `backend/app/sessions/routes.py` (around line 940)

Added Priority 0 (highest priority) for spiral review mode:
```python
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
    else:
        # No more weak cards, exit spiral review mode
        learning_set.spiral_review_mode = False
        db.commit()
        db.refresh(learning_set)
        print("DEBUG: Spiral review completed - no more weak cards")
        # Continue to normal priority selection below

# If not in spiral mode or spiral mode just ended, use normal selection
if not learning_set.spiral_review_mode:
    # Priority 1: Due items (spaced repetition)
    # ... existing priority logic ...
```

#### ✅ 3.3 Enhanced User Messaging
**File:** `backend/app/sessions/routes.py` (around line 760)

Added user-friendly spiral review messaging:
```python
# Check if we're starting a session in spiral review mode
if learning_set and learning_set.spiral_review_mode:
    spiral_config = config
    max_cards = spiral_config.get('spiral_review_max_cards', 20)
    cycles = learning_set.completed_integration_cycles or 0
    learning_message = f"🔄 Spiral Review Active: Reinforcing weak cards from positions 1-{learning_set.current_batch_end} after {cycles} integration cycles. Mastering these will strengthen your long-term retention! 💪"
```
            # Mark current set as completed
            learning_set.status = "completed"
            db.commit()
            
            # Create spiral review learning set
            spiral_learning_set = UserLearningSet(
                user_id=current_user.id,
                dataset_id=learning_set.dataset_id,
                stage=learning_set.stage + 1,
                status="active",
                mode="spiral_review",
                is_spiral_review=True,
                spiral_review_source_range=review_range,
                last_spiral_review_position=learning_set.current_batch_end,
                isolation_phase=False,  # Spiral review is like integration
                current_batch_start=1,
                current_batch_end=len(spiral_cards),
                total_dataset_size=learning_set.total_dataset_size
            )
            db.add(spiral_learning_set)
            db.flush()
            
            # Add spiral review cards
            for i, element in enumerate(spiral_cards):
                item = UserLearningSetItem(
                    learning_set_id=spiral_learning_set.id,
                    element_id=element.id,
                    position=i + 1
                )
                db.add(item)
            
            db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail=f"🌀 Spiral Review triggered! Reinforcing {len(spiral_cards)} weak cards from positions {review_range}. This focused review will strengthen your foundation before continuing with new material! 🧠✨"
            )
    
    # Continue with normal next batch logic if no spiral review
    # ... existing code ...
```

#### 3.2 Add Spiral Review Card Selection Logic
**File:** `backend/app/sessions/routes.py`

In `get_next_flashcard`, add spiral review handling:

```python
# In get_next_flashcard function, after phase detection
if learning_set.mode == "spiral_review":
    # Spiral Review Phase: Focus on weak cards with spaced repetition
    element_ids = [item.element_id for item in learning_set.items]
    
    # Priority 1: Due items from spiral set
    due_reviews = db.query(UserElementReview).filter(
        and_(
            UserElementReview.user_id == current_user.id,
            UserElementReview.element_id.in_(element_ids),
            UserElementReview.next_due <= datetime.utcnow()
        )
    ).order_by(
        # Prioritize by weakness: integration failures, low stability, low accuracy
        UserElementReview.integration_attempts.desc(),
        UserElementReview.stability_score.asc(),
        UserElementReview.accuracy_percentage.asc()
    ).all()
    
    if due_reviews:
        element_id = due_reviews[0].element_id  # Take most critical
    else:
        # Priority 2: Any card in spiral set, prioritized by weakness
        all_spiral_reviews = db.query(UserElementReview).filter(
            and_(
                UserElementReview.user_id == current_user.id,
                UserElementReview.element_id.in_(element_ids)
            )
        ).order_by(
            UserElementReview.integration_attempts.desc(),
            UserElementReview.stability_score.asc(),
            UserElementReview.accuracy_percentage.asc()
        ).all()
        
        if all_spiral_reviews:
            element_id = all_spiral_reviews[0].element_id
        else:
            # Fallback to any element
            element_id = random.choice(element_ids)
```

## Phase 4: Configuration and Admin Interface ✅ COMPLETED

### ✅ Changes Made:

#### 4.1 Updated DEFAULT_LEARNING_CONFIG
**File:** `backend/app/admin/routes.py`

Added spiral learning configuration to the existing `DEFAULT_LEARNING_CONFIG` dictionary:
```python
# Spiral Learning Configuration
"spiral_learning_enabled": {"value": True, "type": "boolean", "description": "Enable spiral learning comprehensive reviews", "category": "spiral_learning"},
"spiral_review_trigger_interval": {"value": 2, "type": "integer", "description": "Number of integration cycles before triggering spiral review", "category": "spiral_learning"},
"spiral_review_max_cards": {"value": 20, "type": "integer", "description": "Maximum number of cards in a spiral review session", "category": "spiral_learning"},
"spiral_weakness_threshold": {"value": 0.6, "type": "float", "description": "Accuracy threshold below which cards are considered weak", "category": "spiral_learning"},
"spiral_stability_threshold": {"value": 1.5, "type": "float", "description": "Stability threshold below which cards are considered weak", "category": "spiral_learning"},
"spiral_integration_failure_weight": {"value": 2.0, "type": "float", "description": "Weight multiplier for cards with integration failures", "category": "spiral_learning"}
```

#### 4.2 Added Spiral Learning Schemas
**File:** `backend/app/admin/schemas.py`

```python
class SpiralConfigUpdate(BaseModel):
    """Spiral Learning Configuration Schema with validation"""
    spiral_learning_enabled: Optional[bool]
    spiral_review_trigger_interval: Optional[int] = Field(None, ge=1, le=5)
    spiral_review_max_cards: Optional[int] = Field(None, ge=5, le=50)
    spiral_weakness_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    spiral_stability_threshold: Optional[float] = Field(None, ge=0.5, le=5.0)
    spiral_integration_failure_weight: Optional[float] = Field(None, ge=1.0, le=10.0)

class SpiralConfigResponse(BaseModel):
    spiral_learning_enabled: bool
    spiral_review_trigger_interval: int
    spiral_review_max_cards: int
    spiral_weakness_threshold: float
    spiral_stability_threshold: float
    spiral_integration_failure_weight: float
```

#### 4.3 Added Three Spiral Learning Admin Endpoints
**File:** `backend/app/admin/routes.py`

1. **GET /admin/config/spiral** - Get spiral learning configuration (admin only)
2. **PUT /admin/config/spiral** - Update spiral learning configuration (admin only) 
3. **POST /admin/config/spiral/reset** - Reset spiral learning config to defaults (admin only)

All endpoints:
- Require admin authentication
- Follow existing patterns from other config endpoints
- Include proper validation and error handling
- Use SystemConfig.get_value/set_value methods
- Support the "spiral_learning" category

### Phase 5: Frontend Integration

#### 5.1 Add Spiral Review UI Indicators
**File:** `frontend/src/pages/Learn.jsx`

Add spiral review detection:
```javascript
// In Learn component
const isSpiralReview = sessionData?.mode === 'spiral_review';

// Add special styling/messaging for spiral review
{isSpiralReview && (
  <div className="spiral-review-banner">
    🌀 Spiral Review Session - Strengthening Foundation
    <p>Focusing on {sessionData.total_items} cards that need reinforcement</p>
  </div>
)}
```

#### 5.2 Add Spiral Review Analytics
**File:** `frontend/src/pages/Learn.jsx`

Track spiral review progress:
```javascript
// Add spiral review stats to progress display
const getSpiralReviewStats = () => {
  if (!isSpiralReview) return null;
  
  return (
    <div className="spiral-stats">
      <span>Spiral Review: {sessionData.spiral_review_source_range}</span>
      <span>Weakness Score: {currentCard?.fsrs_stats?.integration_attempts > 0 ? 'High' : 'Medium'}</span>
    </div>
  );
};
```

## Testing Strategy

### Phase 6: Testing and Validation

#### 6.1 Unit Tests
Create tests for:
- `should_trigger_spiral_review()` logic
- `get_spiral_review_cards()` weakness scoring
- Spiral review session creation
- Integration cycle counting

#### 6.2 Integration Tests
Test complete flow:
1. Complete 2 integration cycles
2. Verify spiral review triggers
3. Complete spiral review
4. Continue normal progression

#### 6.3 User Experience Testing
- Validate spiral review messages are clear
- Ensure spiral review feels like reinforcement, not punishment
- Test spiral review completion and continuation flow

## Configuration Options

### Recommended Settings for Different Use Cases

**Aggressive Reinforcement:**
```
spiral_review_trigger_interval: 1  # After every integration
spiral_review_max_cards: 25
spiral_weakness_threshold: 0.7
```

**Balanced Learning:**
```
spiral_review_trigger_interval: 2  # After every 2 integrations
spiral_review_max_cards: 20
spiral_weakness_threshold: 0.6
```

**Minimal Spiral:**
```
spiral_review_trigger_interval: 3  # After every 3 integrations
spiral_review_max_cards: 15
spiral_weakness_threshold: 0.5
```

## Benefits of This Implementation

1. **Prevents Forgetting Curve:** Regular spiral reviews combat natural forgetting
2. **Targeted Reinforcement:** Focuses on genuinely weak cards, not random review
3. **Adaptive Difficulty:** Cards with integration failures get higher priority
4. **Configurable:** Admins can tune spiral learning intensity
5. **Data-Driven:** Uses actual performance metrics, not arbitrary schedules
6. **Seamless Integration:** Works within existing batch-integration flow
7. **User-Friendly:** Clear messaging about why spiral review is happening

## Implementation Priority

1. **Phase 1** (Database): Essential foundation
2. **Phase 2** (Core Logic): Spiral detection and card selection
3. **Phase 3** (Integration): Hook into existing flow
4. **Phase 4** (Configuration): Admin controls
5. **Phase 5** (Frontend): User experience
6. **Phase 6** (Testing): Validation and refinement

This spiral learning enhancement transforms our system from simple batch progression to a sophisticated, research-based learning platform that actively combats forgetting and reinforces weak points!
