"""
Spaced Repetition Algorithms

Implementation of various spaced repetition algorithms including SM-2, FSRS, and custom algorithms.
"""
from datetime import datetime, timedelta
from typing import List, Tuple
import math


class SM2Algorithm:
    """Implementation of the SM-2 (SuperMemo 2) spaced repetition algorithm"""
    
    def __init__(self, config=None):
        """Initialize with configuration parameters"""
        if config:
            self.initial_ease = config.initial_ease
            self.minimum_ease = config.minimum_ease
            self.maximum_ease = config.maximum_ease
            self.ease_bonus = config.ease_bonus
            self.ease_penalty = config.ease_penalty
            self.initial_interval = config.initial_interval
            self.graduation_interval = config.graduation_interval
            self.maximum_interval = config.maximum_interval
        else:
            # Default parameters
            self.initial_ease = 2.5
            self.minimum_ease = 1.3
            self.maximum_ease = 5.0
            self.ease_bonus = 0.15
            self.ease_penalty = 0.2
            self.initial_interval = 1
            self.graduation_interval = 6  # Standard SM-2: second review at 6 days
            self.maximum_interval = 365
    
    def calculate_next_interval(self, ease_factor: float, repetition: int, was_correct: bool,
                              previous_interval: int = None,
                              response_quality: int = None) -> Tuple[int, float, int]:
        """
        Calculate the next review interval and updated ease factor.

        Args:
            ease_factor: Current ease factor (2.5 default)
            repetition: Number of successful repetitions so far
            was_correct: Whether the answer was correct
            previous_interval: The interval used for the most recent review (required
                               when repetition >= 2 so the exponential growth is correct)
            response_quality: Quality of response (0-5, where 3+ is correct)

        Returns:
            Tuple of (next_interval_days, new_ease_factor, new_repetition)
        """
        if response_quality is None:
            response_quality = 4 if was_correct else 2

        new_ease = ease_factor

        if response_quality >= 3:  # Correct answer
            if repetition == 0:
                interval = self.initial_interval
            elif repetition == 1:
                interval = self.graduation_interval
            else:
                # SM-2: next interval = previous_interval * EF (exponential growth)
                prev = previous_interval if previous_interval is not None else self.graduation_interval
                interval = math.ceil(prev * ease_factor)

            # Adjust ease factor based on response quality (standard SM-2 formula)
            new_ease = ease_factor + (0.1 - (5 - response_quality) * (0.08 + (5 - response_quality) * 0.02))
            new_ease = min(max(new_ease, self.minimum_ease), self.maximum_ease)

            repetition += 1
        else:  # Incorrect answer
            repetition = 0
            interval = self.initial_interval
            new_ease = max(ease_factor - self.ease_penalty, self.minimum_ease)

        # Cap the interval at maximum
        interval = min(interval, self.maximum_interval)

        return interval, new_ease, repetition
    
    def get_learning_steps(self, steps_string: str) -> List[int]:
        """Parse learning steps from configuration string"""
        try:
            return [int(step) for step in steps_string.split(',')]
        except:
            return [1, 10, 1440]  # Default: 1min, 10min, 1day


class FSRSAlgorithm:
    """
    Implementation of the FSRS 4.5 spaced repetition algorithm.

    Ratings:  1=Again  2=Hard  3=Good  4=Easy
    State:    stability (S) — days until 90% retention
              difficulty (D) — 1 (easy) to 10 (hard)
    """

    def __init__(self, desired_retention: float = 0.9, maximum_interval: int = 365):
        # Pre-trained FSRS 4.5 default weights
        self.w = [
            0.5701, 1.4436, 4.1386, 10.9355, 5.1443, 1.2006, 0.8627, 0.0362,
            1.629,  0.1342, 1.0166, 2.1174,  0.0839, 0.3204, 1.4676, 0.219,  2.8237
        ]
        self.desired_retention = desired_retention
        self.maximum_interval = maximum_interval

    # ------------------------------------------------------------------
    # New-card initialisation
    # ------------------------------------------------------------------

    def initial_stability(self, rating: int) -> float:
        """Initial stability S0 for a brand-new card, indexed by rating (1–4)."""
        return self.w[rating - 1]

    def initial_difficulty(self, rating: int) -> float:
        """Initial difficulty D0 for a brand-new card.  D0 = w[4] - (r-3)*w[5]."""
        return min(max(self.w[4] - (rating - 3) * self.w[5], 1.0), 10.0)

    # ------------------------------------------------------------------
    # Per-review updates
    # ------------------------------------------------------------------

    def update_difficulty(self, difficulty: float, rating: int) -> float:
        """Mean-reversion difficulty update.  D' = D - w[6]*(r-3), clamped [1, 10]."""
        return min(max(difficulty - self.w[6] * (rating - 3), 1.0), 10.0)

    def calculate_retrievability(self, elapsed_days: float, stability: float) -> float:
        """Power forgetting curve: R(t, S) = (1 + t / (9·S))^-1."""
        return math.pow(1.0 + elapsed_days / (9.0 * stability), -1.0)

    def calculate_stability(self, difficulty: float, stability: float,
                            retrievability: float, rating: int) -> float:
        """New stability after a review (FSRS 4.5 recall/forget branches)."""
        if rating >= 2:  # Hard / Good / Easy  — successful recall
            new_s = stability * (
                1.0 + math.exp(self.w[8])
                * (11.0 - difficulty)
                * math.pow(stability, -self.w[9])
                * (math.exp((1.0 - retrievability) * self.w[10]) - 1.0)
            )
        else:  # Again — forgotten
            new_s = (
                self.w[11]
                * math.pow(difficulty, -self.w[12])
                * (math.pow(stability + 1.0, self.w[13]) - 1.0)
                * math.exp((1.0 - retrievability) * self.w[14])
            )
        return max(new_s, 0.01)

    def next_interval(self, stability: float) -> int:
        """
        Interval (days) that achieves desired_retention.
        Derived from R = (1 + t/9S)^-1  →  t = 9S·(1/R - 1)
        """
        interval = 9.0 * stability * (1.0 / self.desired_retention - 1.0)
        return min(max(1, round(interval)), self.maximum_interval)

    # ------------------------------------------------------------------
    # Unified entry point
    # ------------------------------------------------------------------

    def review(self, stability: float, difficulty: float,
               elapsed_days: float, rating: int) -> Tuple[float, float, int]:
        """
        Process one review and return updated card state.

        Args:
            stability:    current S (days to desired retention)
            difficulty:   current D (1–10)
            elapsed_days: days since last review
            rating:       1=Again 2=Hard 3=Good 4=Easy

        Returns:
            (new_stability, new_difficulty, next_interval_days)
        """
        retrievability = self.calculate_retrievability(elapsed_days, stability)
        new_stability = self.calculate_stability(difficulty, stability, retrievability, rating)
        new_difficulty = self.update_difficulty(difficulty, rating)
        interval = self.next_interval(new_stability)
        return new_stability, new_difficulty, interval


def compute_fsrs_rating(is_correct: bool, response_time_ms: int,
                        fast_threshold_ms: int = 3000,
                        slow_threshold_ms: int = 8000) -> int:
    """
    Map a binary correct/wrong answer + response time to an FSRS rating (1–4).

    Rating  Meaning   Condition
    ------  -------   ---------
    1       Again     Wrong answer
    2       Hard      Correct but slow  (> slow_threshold_ms)
    3       Good      Correct, normal speed (fast_threshold_ms – slow_threshold_ms)
    4       Easy      Correct and fast  (< fast_threshold_ms)

    Args:
        is_correct:        whether the user got the answer right
        response_time_ms:  time taken in milliseconds
        fast_threshold_ms: upper bound for "Easy" (default 3 s)
        slow_threshold_ms: lower bound for "Hard"  (default 8 s)

    Returns:
        int in range [1, 4]
    """
    if not is_correct:
        return 1  # Again
    if response_time_ms < fast_threshold_ms:
        return 4  # Easy
    if response_time_ms <= slow_threshold_ms:
        return 3  # Good
    return 2  # Hard


def calculate_card_difficulty(attempts: List) -> float:
    """
    Calculate difficulty score for a card based on user attempts
    
    Args:
        attempts: List of UserFieldAttempt objects
    
    Returns:
        Difficulty score between 0.0 (easy) and 1.0 (very difficult)
    """
    if not attempts:
        return 0.5  # Default difficulty
    
    # Calculate error rate
    correct_count = sum(1 for attempt in attempts if attempt.is_correct)
    error_rate = 1.0 - (correct_count / len(attempts))
    
    # Calculate average response time (if available)
    response_times = [a.response_time_ms for a in attempts if a.response_time_ms and a.response_time_ms > 0]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 5000  # 5s default
    
    # Normalize response time (assume 1-10 seconds is normal range)
    normalized_time = min(max((avg_response_time / 1000.0 - 1) / 9, 0), 1)
    
    # Calculate recent performance trend
    recent_attempts = attempts[-10:] if len(attempts) >= 10 else attempts
    recent_correct = sum(1 for attempt in recent_attempts if attempt.is_correct)
    recent_accuracy = recent_correct / len(recent_attempts) if recent_attempts else 0.5
    recent_error_rate = 1.0 - recent_accuracy
    
    # Weighted difficulty score
    # 50% error rate, 30% response time, 20% recent trend
    difficulty = (
        error_rate * 0.5 + 
        normalized_time * 0.3 + 
        recent_error_rate * 0.2
    )
    
    return min(max(difficulty, 0.0), 1.0)


def calculate_optimal_retention_rate(user_performance_data: dict) -> float:
    """
    Calculate optimal retention rate based on user's learning pattern
    
    Args:
        user_performance_data: Dictionary with user performance metrics
    
    Returns:
        Optimal retention rate between 0.8 and 0.95
    """
    # Default retention rate
    base_retention = 0.9
    
    # Adjust based on accuracy
    accuracy = user_performance_data.get('accuracy', 0.8)
    if accuracy > 0.9:
        # High performer - can handle lower retention for more reviews
        retention_adjustment = -0.05
    elif accuracy < 0.7:
        # Struggling learner - increase retention
        retention_adjustment = 0.05
    else:
        retention_adjustment = 0.0
    
    # Adjust based on study frequency
    daily_reviews = user_performance_data.get('daily_reviews', 20)
    if daily_reviews > 50:
        # High volume - slightly lower retention to manage load
        retention_adjustment -= 0.02
    elif daily_reviews < 10:
        # Low volume - can afford higher retention
        retention_adjustment += 0.02
    
    optimal_retention = base_retention + retention_adjustment
    return min(max(optimal_retention, 0.8), 0.95)


def calculate_learning_velocity(attempts: List) -> float:
    """
    Calculate how quickly a user learns a particular card
    
    Args:
        attempts: List of UserFieldAttempt objects in chronological order
    
    Returns:
        Learning velocity multiplier (0.5 = slow, 1.0 = normal, 2.0 = fast)
    """
    if len(attempts) < 3:
        return 1.0  # Default velocity
    
    # Look at improvement over time
    early_attempts = attempts[:len(attempts)//2]
    late_attempts = attempts[len(attempts)//2:]
    
    early_accuracy = sum(1 for a in early_attempts if a.is_correct) / len(early_attempts)
    late_accuracy = sum(1 for a in late_attempts if a.is_correct) / len(late_attempts)
    
    improvement = late_accuracy - early_accuracy
    
    # Convert improvement to velocity multiplier
    if improvement > 0.3:
        return 2.0  # Fast learner
    elif improvement > 0.1:
        return 1.5  # Above average
    elif improvement > -0.1:
        return 1.0  # Average
    elif improvement > -0.3:
        return 0.75  # Below average
    else:
        return 0.5  # Slow learner
