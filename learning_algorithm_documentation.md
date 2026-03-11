# Learning Algorithm Documentation
## Comprehensive Technical Reference

### Table of Contents
1. [Overview](#overview)
2. [Core Learning Algorithms](#core-learning-algorithms)
3. [Data Models & Tracked Variables](#data-models--tracked-variables)
4. [Learning System Configuration](#learning-system-configuration)
5. [Session Management](#session-management)
6. [Progress Tracking](#progress-tracking)
7. [Performance Analytics](#performance-analytics)

---

## Overview

The flashcard learning system implements an adaptive, multi-layered approach combining spaced repetition with chunked learning strategies. The system automatically adjusts based on dataset size and user performance, using confidence-based progress display and comprehensive performance tracking.

### Key Features
- **Adaptive Chunk Sizing**: Dynamic chunk sizes based on dataset size (100→75→60→50 progression)
- **Spaced Repetition Algorithm**: Modified SuperMemo-inspired algorithm with ease factor adjustments
- **Confidence-Based Progress**: Visual progress display showing Strong/Weak/New card categories
- **Performance Analytics**: Detailed tracking of response times, accuracy, and learning patterns
- **Multi-Tier Learning**: Automatic switching between chunked, progressive, and immediate learning modes

---

## Core Learning Algorithms

### 1. Spaced Repetition Algorithm

The system uses a modified SuperMemo algorithm with the following mechanics:

#### Algorithm Parameters
- **Initial Ease Factor**: 2.5 (stored as 250, integer × 100)
- **Mastery Threshold**: 3 consecutive correct answers (configurable)
- **Ease Factor Range**: 1.3 - 3.0 (130 - 300 when stored as integer)
- **Maximum Interval**: 365 days (1 year cap)

#### Success Path (Correct Answer)
```python
# Increment success streak
review.success_streak += 1

# Check mastery threshold
if review.success_streak >= mastery_threshold:
    review.status = "mastered"
    review.interval_days = min(review.interval_days * 2, 365)  # Double interval, cap at 1 year
else:
    review.status = "learning"
    review.interval_days = review.success_streak  # 1, 2, 3 days progressive

# Ease factor adjustment (slight improvement)
review.ease_factor = min(review.ease_factor + 5, 300)  # +0.05, cap at 3.0
```

#### Failure Path (Incorrect Answer)
```python
# Reset progress
review.success_streak = 0
review.status = "learning"
review.interval_days = 1
review.is_difficult = True

# Ease factor penalty (significant reduction)
review.ease_factor = max(review.ease_factor - 20, 130)  # -0.2, floor at 1.3
```

#### Next Due Date Calculation
```python
ease = review.ease_factor / 100.0  # Convert to decimal
review.next_due = datetime.utcnow() + timedelta(days=review.interval_days * ease)
```

### 2. Chunked Learning System

For datasets >100 cards, the system implements adaptive chunked learning:

#### Chunk Size Progression
- **Default Progression**: "100,75,60,50" (configurable)
- **Adaptive Sizing**: Decreasing chunk sizes for better retention
- **Formula**: 
  ```python
  def get_adaptive_chunk_size(chunk_number: int, chunk_progression: str) -> int:
      sizes = [int(x.strip()) for x in chunk_progression.split(',')]
      return sizes[min(chunk_number - 1, len(sizes) - 1)]
  ```

#### Chunk Management
- **Automatic Progression**: Chunk completion triggers next chunk creation
- **Status Tracking**: Each chunk tracks completion independently
- **Element Distribution**: Elements distributed sequentially across chunks

### 3. Multi-Tier Learning Strategy

The system automatically selects learning mode based on dataset size:

#### Tier 1: Immediate Learning (≤15 cards)
- **Mode**: Show all cards at once
- **Stage Increment**: 0 (no progression)
- **Rationale**: Small sets don't require chunking

#### Tier 2: Progressive Learning (16-100 cards)
- **Initial Size**: Configurable (default: based on dataset size)
- **Stage Increment**: 10 cards (configurable)
- **Progression**: Gradual introduction of new cards

#### Tier 3: Chunked Learning (>100 cards)
- **Chunk System**: Adaptive sizing with progression
- **Stage Increment**: 10 cards within each chunk
- **Management**: Automatic chunk transitions

---

## Data Models & Tracked Variables

### 1. UserLearningSet Model

Primary learning session container with adaptive configuration.

```python
class UserLearningSet(Base):
    id: UUID                    # Unique session identifier
    user_id: UUID              # User ownership
    dataset_id: UUID           # Source dataset reference
    stage: int = 15            # Current learning stage (cards visible)
    chunk_size: int            # Adaptive chunk sizing
    chunk_number: Optional[int] # Current chunk (1-based)
    total_chunks: Optional[int] # Total chunks in dataset
    total_dataset_size: int    # Complete dataset size
    status: str = "active"     # active/completed/paused
    created_at: datetime       # Session creation timestamp
    updated_at: datetime       # Last modification timestamp
```

**Key Variables Explained**:
- `stage`: Controls how many cards are visible in current learning phase
- `chunk_size`: Dynamic sizing based on learning progression algorithm
- `chunk_number`/`total_chunks`: Enable chunked learning for large datasets

### 2. UserElementReview Model

Core spaced repetition tracking with comprehensive performance data.

```python
class UserElementReview(Base):
    id: UUID                        # Unique review record
    user_id: UUID                  # User ownership
    element_id: UUID               # Flashcard element reference
    success_streak: int = 0        # Consecutive correct answers
    review_count: int = 0          # Total review attempts
    status: str = "new"            # new/learning/mastered
    is_difficult: bool = False     # Difficulty flag for failed cards
    ease_factor: int = 250         # Spaced repetition ease (2.5 * 100)
    interval_days: int = 1         # Days until next review
    next_due: datetime             # Calculated next review date
    last_reviewed: Optional[datetime] # Last review timestamp
    created_at: datetime           # First encounter timestamp
    updated_at: datetime           # Last modification timestamp
```

**Critical Variables Explained**:
- `success_streak`: Core spaced repetition counter, resets to 0 on failure
- `ease_factor`: Stored as integer × 100 (250 = 2.5 ease factor)
- `interval_days`: Base interval modified by ease factor for next_due calculation
- `is_difficult`: Permanent flag for cards that have been answered incorrectly
- `status`: Learning phase indicator affecting card selection priority

### 3. UserFieldAttempt Model

Detailed answer tracking for performance analytics and learning insights.

```python
class UserFieldAttempt(Base):
    id: UUID                       # Unique attempt record
    user_id: UUID                 # User ownership
    element_id: UUID              # Flashcard element reference
    question_field_id: UUID       # Question field reference
    answer_field_id: UUID         # Answer field reference
    user_answer: Optional[str]    # User's submitted answer
    is_correct: bool              # Correctness assessment
    response_time_ms: Optional[int] # Time to answer (milliseconds)
    created_at: datetime          # Attempt timestamp
```

**Analytics Variables Explained**:
- `response_time_ms`: Performance metric for learning speed analysis
- `user_answer`: Captures actual responses for review and analysis
- `question_field_id`/`answer_field_id`: Enable multi-field flashcard support
- `is_correct`: Binary success tracking for accuracy calculations

---

## Learning System Configuration

### Configurable Parameters

All learning parameters are stored in `SystemConfig` table and can be dynamically adjusted:

```python
# Core Algorithm Settings
DEFAULT_MASTERY_THRESHOLD = 3        # Consecutive correct answers for mastery
DEFAULT_STAGE_INCREMENT = 10         # Cards added per stage progression
DEFAULT_INITIAL_STAGE = 15          # Starting number of visible cards
DEFAULT_MID_TIER_THRESHOLD = 50     # Boundary for progressive learning
DEFAULT_MAX_SET_SIZE = 100          # Boundary for chunked learning

# Chunked Learning Configuration
DEFAULT_CHUNK_PROGRESSION = "100,75,60,50"  # Adaptive chunk sizes
```

### Learning Mode Selection Logic

```python
def get_learning_config(db: Session) -> dict:
    """Dynamic learning configuration based on dataset size"""
    
    if total_elements <= 15:
        return {
            'initial_stage': total_elements,
            'stage_increment': 0,         # No progression needed
            'is_chunked': False,
        }
    elif total_elements <= mid_tier_threshold:
        return {
            'initial_stage': base_config['initial_stage'],
            'stage_increment': base_config['stage_increment'],
            'is_chunked': False,
        }
    elif total_elements <= max_set_size:
        return {
            'initial_stage': base_config['initial_stage'],
            'stage_increment': base_config['stage_increment'], 
            'is_chunked': False,
        }
    else:  # Chunked learning for large datasets
        return {
            'chunk_size_progression': base_config['chunk_size_progression'],
            'stage_increment': base_config['stage_increment'],
            'is_chunked': True,
        }
```

---

## Session Management

### Card Selection Priority System

The system uses a sophisticated priority system for card selection:

#### Priority 1: Due Cards (Spaced Repetition)
```python
due_reviews = db.query(UserElementReview).filter(
    and_(
        UserElementReview.user_id == current_user.id,
        UserElementReview.element_id.in_(element_ids),
        UserElementReview.next_due <= datetime.utcnow(),
        UserElementReview.status != "mastered"
    )
).all()
```

#### Priority 2: New Cards (Never Reviewed)
```python
reviewed_element_ids = db.query(UserElementReview.element_id).filter(
    and_(
        UserElementReview.user_id == current_user.id,
        UserElementReview.element_id.in_(element_ids)
    )
).all()
reviewed_ids = [r[0] for r in reviewed_element_ids]
new_element_ids = [eid for eid in element_ids if eid not in reviewed_ids]
```

#### Priority 3: Session Completion Detection
- **Chunked Learning**: Automatic progression to next chunk
- **Progressive Learning**: Stage increment when current stage mastered
- **Completion**: All cards mastered triggers session completion

### Session State Management

```python
# Session completion logic
mastered_count = db.query(func.count(UserElementReview.id)).filter(
    and_(
        UserElementReview.user_id == current_user.id,
        UserElementReview.element_id.in_(element_ids),
        UserElementReview.status == "mastered"
    )
).scalar() or 0

# Check completion conditions
if mastered_count >= len(element_ids):
    if is_chunked_learning:
        await start_next_chunk(db, learning_set, current_user)
    else:
        learning_set.status = "completed"
```

---

## Progress Tracking

### Confidence-Based Progress Display

The system categorizes cards into confidence levels for meaningful progress visualization:

#### Confidence Categories
```python
def calculate_confidence_stats(element_ids, user_reviews):
    """
    Strong: success_streak >= 2 (mastered or nearly mastered)
    Weak: success_streak == 1 (learning but struggling) 
    New: never reviewed (completely unknown)
    """
    
    strong_cards = sum(1 for r in user_reviews if r.success_streak >= 2)
    weak_cards = sum(1 for r in user_reviews if r.success_streak == 1)
    new_cards = len(element_ids) - len(user_reviews)
    
    return {
        'strong_count': strong_cards,
        'weak_count': weak_cards, 
        'new_count': new_cards,
        'total_cards': len(element_ids)
    }
```

#### Progress Message Generation
```python
# Learning phase determination
if strong_count >= total_cards * 0.8:
    learning_message = "Nearly mastered"
elif strong_count >= total_cards * 0.6:
    learning_message = "Building mastery"
elif strong_count >= total_cards * 0.4:
    learning_message = "Making progress"
else:
    learning_message = "Getting started"
```

### Visual Progress Components

The frontend displays multi-segment progress bars showing:
- **Strong Cards**: Green segments for confident knowledge
- **Weak Cards**: Yellow segments for partial knowledge
- **New Cards**: Gray segments for unlearned material
- **Learning Message**: Contextual progress description

---

## Performance Analytics

### Session Statistics Tracking

Real-time performance metrics collected during learning sessions:

```javascript
// Frontend session statistics
const [sessionStats, setSessionStats] = useState({
    correctAnswers: 0,
    incorrectAnswers: 0,
    totalAnswers: 0,
    accuracy: 0
});

// Update on each answer submission
const updateSessionStats = (isCorrect) => {
    setSessionStats(prev => {
        const correct = prev.correctAnswers + (isCorrect ? 1 : 0);
        const incorrect = prev.incorrectAnswers + (isCorrect ? 0 : 1);
        const total = correct + incorrect;
        
        return {
            correctAnswers: correct,
            incorrectAnswers: incorrect,
            totalAnswers: total,
            accuracy: total > 0 ? Math.round((correct / total) * 100) : 0
        };
    });
};
```

### Backend Analytics Tracking

Comprehensive data collection for learning analysis:

```python
# UserFieldAttempt creation for each answer
field_attempt = UserFieldAttempt(
    user_id=current_user.id,
    element_id=element_id,
    question_field_id=question_field.id,
    answer_field_id=answer_field.id,
    user_answer=request.user_answer,
    is_correct=request.is_correct,
    response_time_ms=response_time_ms,
    created_at=datetime.utcnow()
)
```

### Performance Metrics Available

1. **Response Times**: Millisecond precision for speed analysis
2. **Accuracy Tracking**: Correct/incorrect ratios per session
3. **Learning Velocity**: Cards mastered per time unit
4. **Difficulty Patterns**: Cards marked as difficult for review
5. **Retention Curves**: Success rates over spaced intervals
6. **Session Performance**: Real-time accuracy feedback

---

## Implementation Notes

### Database Schema Relationships
- **UserLearningSet** ↔ **UserLearningSetItem**: One-to-many for chunk management
- **UserElementReview** ↔ **Element**: One-to-one for spaced repetition tracking
- **UserFieldAttempt** ↔ **UserElementReview**: Many-to-one for detailed attempt history

### Performance Optimizations
- **Indexed Queries**: Optimized database queries for card selection
- **Batch Processing**: Chunked data processing for large datasets
- **Caching Strategy**: Configuration caching to reduce database calls
- **Efficient Filtering**: SQL-level filtering for due card selection

### Scalability Considerations
- **Chunked Processing**: Handles datasets of unlimited size
- **Adaptive Algorithms**: Performance scales with user proficiency
- **Configurable Parameters**: System tuning without code changes
- **Background Processing**: Non-blocking operations for large operations

---

*This documentation covers the complete learning algorithm implementation as of the current system state. The algorithm combines proven spaced repetition techniques with modern adaptive learning strategies to provide an optimal flashcard learning experience.*
