# Adaptive Learning Algorithm for LLM-based Memorization

## Overview

This document outlines a five-phase adaptive learning algorithm inspired by memory science (spacing effect, testing effect, interleaving, etc.) for use in a flashcard-based memorization system. All parameters are configurable, and the system is designed to interact with an LLM to manage card presentation, evaluation, and progression.

## Global Parameters

- `N_CARDS_PER_SET`: Number of new cards per learning set (e.g., 5)
- `PASS_THRESHOLD`: Minimum percentage of correct fields to pass a card (e.g., 70%)
- `MAX_SETS_IN_ISOLATION`: Number of completed sets to review together in isolation (e.g., 2)
- `MAX_ERROR_RATE_SPIRAL`: Maximum tolerated error rate in Spiral Review (e.g., 20%)
- `MIN_DAYS_BETWEEN_PHASES`: Minimum wait time before a card can be promoted to next phase (e.g., 1 day)
- `RETRIEVAL_DIFFICULTY_SCALE`: {"Easy", "Moderate", "Hard"}
- `FIELD_CONFIDENCE_LEVELS`: {"Low", "Medium", "High"}

## Phases

### 1. Learning

**Goal**: Establish foundational recall for each field in a card.

Steps:
1. Select a new random set of `N_CARDS_PER_SET` cards.
2. For each card:
   - Ask all fields in random order.
   - Insert micro-retrieval questions during session (testing effect).
   - Collect accuracy, retrieval difficulty, and confidence per field.
3. Mark card as complete if `PASS_THRESHOLD` is met.
4. If fewer than `MAX_SETS_IN_ISOLATION` sets complete, repeat with new set.
5. If maximum sets complete, delay `MIN_DAYS_BETWEEN_PHASES` then proceed to Isolation.

### 2. Isolation

**Goal**: Strengthen memory through randomized, repeated recall of mastered cards.

Steps:
1. Merge and shuffle last `MAX_SETS_IN_ISOLATION` completed learning sets.
2. For each card:
   - Ask all fields in random order.
   - Record correctness, difficulty, and confidence.
3. Mark cards as completed when accuracy >= `PASS_THRESHOLD` and min time met.
4. When all cards pass, return to Learning with a new set.
5. When all cards in dataset are completed → proceed to Integration.

### 3. Integration

**Goal**: Apply interleaved, one-time recall for realism.

Steps:
1. Pool all cards from completed Isolation phase.
2. Randomize all cards and fields.
3. Ask each field **once only**.
4. Use distractors from **same field** of other cards only.
5. Record correctness and confidence.

### 4. Spiral Review

**Goal**: Target weak areas with spaced, mixed-context recall.

Steps:
1. Identify most failed or overconfident fields.
2. Present again with distractors (same field, other cards).
3. Mix in mastered cards as distractors (context interference).
4. Repeat until error rate < `MAX_ERROR_RATE_SPIRAL`.

### 5. Retention / Completion

**Goal**: Maintain long-term memory.

Steps:
1. Use a time-based schedule to revisit cards.
2. Apply adaptive reactivation intervals based on prior performance.
3. Display visual indicators of stability and review progress.

## Visual Feedback Components

- Phase timeline per card
- Field-level mastery heatmap
- Confidence trend chart
- Spacing interval tracker

## Notes

- All transitions between phases should respect configured delays.
- Card metadata must track: current phase, per-field performance, timestamps, and retrieval difficulty.

---
Generated on 2025-08-22
