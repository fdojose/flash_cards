# User Journey

Describes the expected behavior of a user moving through the flashcard system and the expected system responses at each step. All values reflect default configuration.

---

## Default Configuration Reference

| Parameter | Default | Meaning |
|-----------|---------|---------|
| Batch size | 5 | Cards introduced per isolation batch |
| Isolation mastery: min attempts | 3 | Attempts in review window before mastery is evaluated |
| Isolation mastery: accuracy | ≥ 80% | Fraction of those attempts that must be correct |
| Isolation mastery: streak | ≥ 2 consecutive | Trailing correct answers required |
| Integration confirmation: attempts | 1 | Attempts needed to confirm in integration |
| Integration confirmation: accuracy | 100% | Must get it right on the first integration attempt |
| Integration max failures | 3 | Failures before card is sent back to `learning` |
| Spiral review trigger | every 2 integration cycles | |
| **FSRS: desired_retention** | **0.9** | **Target probability of recall at review time (0.8–0.95)** |
| **FSRS: maximum_interval** | **365 days** | **Hard cap on scheduled interval** |
| **FSRS: fast_threshold_ms** | **3 000 ms** | **Response time below which rating = Easy (4)** |
| **FSRS: slow_threshold_ms** | **8 000 ms** | **Response time above which rating = Hard (2)** |

---

## Phase Overview

```
New batch (5 cards)
    └─► ISOLATION PHASE
            Each card: new → learning → isolation_mastered
            When all 5 reach isolation_mastered:
                └─► INTEGRATION PHASE
                        All mastered cards together
                        Each card: isolation_mastered → integration_review → integration_confirmed
                        When all confirmed:
                            └─► Next batch of 5 added → back to ISOLATION PHASE
                                    (Spiral review triggered every 2 integration cycles)
```

---

## Step 1 — Registration & Login

**User does:** registers with email + password, then logs in.

**System responds:**
- `POST /auth/register` → creates user record, hashes password with bcrypt.
- `POST /auth/login` → returns a JWT access token (30-minute expiry by default).
- All subsequent requests require `Authorization: Bearer <token>`.

---

## Step 2 — Start a Session

**User does:** selects a dataset and calls `POST /sessions/start`.

**System responds:**
- Checks if an active `UserLearningSet` exists for this user + dataset.
- If none: creates one with `isolation_phase=True`, `current_batch_start=1`, `current_batch_end=5`, `batch_size=5`.
- Picks the first 5 elements from the dataset (by insertion order), creates `UserLearningSetItem` records with positions 1–5.
- Returns `learning_set_id`, stage info, and the list of element IDs in the batch.

---

## Step 3 — Isolation Phase (Batch 1, cards 1–5)

The user studies only these 5 cards until each reaches `isolation_mastered`.

### FSRS rating system

Every answer is mapped to one of four FSRS ratings based on correctness and response time:

| Rating | Name  | Condition |
|--------|-------|-----------|
| 1 | **Again** | Wrong answer |
| 2 | **Hard**  | Correct but slow (> 8 s) |
| 3 | **Good**  | Correct, normal speed (3–8 s) |
| 4 | **Easy**  | Correct and fast (< 3 s) |

Thresholds (3 s / 8 s) are configurable in `SpacedRepetitionConfig`.

### FSRS state per card

Each card tracks two values that drive scheduling:

| Field | Meaning | Initial value (rating=Good) |
|-------|---------|-----------------------------|
| `stability_score` (S) | Days until retrievability drops to `desired_retention` | w[2] ≈ 4.14 |
| `difficulty` (D) | Card hardness on scale 1–10 | w[4] ≈ 5.14 |

Retrievability at review time: `R = (1 + elapsed / (9·S))^-1`

### Card lifecycle within isolation

**Card status progression:**

```
new ──► learning ──► isolation_mastered
```

A card starts as `new`. After the first answer it becomes `learning`. The classification system evaluates `isolation_mastered` once the review window has enough data:

| Condition | Threshold |
|-----------|-----------|
| Total attempts in window | ≥ 3 |
| Accuracy across those attempts | ≥ 80% |
| Trailing consecutive correct answers | ≥ 2 |

Example: attempts = [correct, wrong, correct, correct]
→ accuracy = 3/4 = 75% — **not mastered** (below 80%)

Example: attempts = [correct, correct, correct]
→ accuracy = 3/3 = 100%, streak = 3 — **mastered** ✓

### `GET /sessions/next` card selection priority (isolation phase)

1. **Due cards** (`next_due ≤ now`, status not `isolation_mastered`)
2. **New cards** (never seen, status `new`)
3. **Any non-mastered card** as fallback

### Scheduling during isolation (short-interval overrides — FSRS not active yet)

FSRS state (S, D) is **initialised** on the first answer but **not advanced** during isolation. Real spaced intervals only begin in integration, where the user has actually waited between reviews.

`next_due` is overridden to keep cards in fast circulation:

| `success_streak` | `next_due` |
|-----------------|------------|
| 0 or 1 | now + **10 minutes** |
| 2 or 3 | now + **1 hour** |
| ≥ 4 | now + **1 day** (hard cap) |

> Streak increments on rating ≥ 2 (Hard/Good/Easy) and resets on rating 1 (Again).

### FSRS initialisation trace (first encounter, rating = Good = 3)

| Event | Rating | `success_streak` | S (stability) | D (difficulty) | `next_due` |
|-------|--------|-----------------|---------------|----------------|------------|
| Start | — | 0 | — | — | — |
| Answer #1 | Good (3) | 1 | 4.139 | 5.144 | now + 10 min |
| Answer #2 | Good (3) | 2 | (unchanged) | (unchanged) | now + 1 hr |
| Answer #3 | Easy (4) | 3 | (unchanged) | (unchanged) | now + 1 hr |
| Answer #4 | Good (3) | 4 | (unchanged) | (unchanged) | now + 1 day |
| **Again (1)** | Again (1) | 0 | (unchanged) | (unchanged) | now + 10 min |
| Answer | Good (3) | 1 | (unchanged) | (unchanged) | now + 10 min |

S and D are frozen until the card graduates to integration.

### `POST /sessions/answer` response (isolation phase)

```json
{
  "correct": true,
  "success_streak": 2,
  "status": "learning",
  "next_due": "<now + 1 hour>",
  "explanation": "Learning | Accuracy: 100.0% (Isolation), Streak: 2"
}
```

When mastered:
```json
{
  "correct": true,
  "success_streak": 3,
  "status": "isolation_mastered",
  "next_due": "<now + 1 day>",
  "explanation": "Mastered | Accuracy: 100.0% (Isolation), Streak: 3"
}
```

---

## Step 4 — Batch 1 Fully Mastered → Integration Phase Begins

**Trigger:** all 5 cards in the current batch reach `isolation_mastered`.

**System does:**
- Sets `learning_set.isolation_phase = False`.
- Sets `learning_set.mastered_up_to = 5` (positions 1–5 are now eligible for integration).
- Does **not** yet add new cards — integration happens first.

---

## Step 5 — Integration Phase (cards 1–5 reviewed together)

Cards from the isolation batch are now reviewed against each other (mixed context). Each card must be **confirmed** in this phase before the next batch opens.

### Card status in integration

```
isolation_mastered ──► integration_review ──► integration_confirmed
                                │
                                └─► (after 3 failures) ──► learning (back to isolation)
```

**On first encounter in integration:**
Card status: `isolation_mastered` with no `last_integration_attempt` → transitions to `integration_review`.

**Confirmation attempt:**
The card needs **1 attempt** with **100% accuracy** to become `integration_confirmed`.

| Outcome | System response |
|---------|----------------|
| Correct | → `integration_confirmed`, stability score ×1.1 |
| Wrong | → stays `integration_review`, `integration_attempts` +1 |
| 3rd wrong | → back to `learning`, stability score ×0.8 |

### Scheduling in integration (full FSRS, no override)

```
next_due = now + interval_days
interval_days = 9·S·(1/desired_retention − 1)
```

FSRS updates S and D on every answer. The interval grows as stability increases, shrinks on Again. `desired_retention=0.9` means each card is reviewed just before its recall probability would drop below 90%.

### FSRS integration trace (starting from S=4.14, D=5.14, desired_retention=0.9)

| Answer | Rating | Elapsed | R (retrievability) | S (new) | D (new) | Interval |
|--------|--------|---------|-------------------|---------|---------|----------|
| 1 | Good (3) | 0 d | 1.000 | ~11.2 | 5.14 | ~11 d |
| 2 | Good (3) | 11 d | 0.901 | ~25.8 | 5.14 | ~26 d |
| 3 | Easy (4) | 26 d | 0.900 | ~65.3 | 4.28 | ~65 d |
| 4 | Again (1) | 65 d | 0.889 | ~4.1 | 5.14 | ~4 d |
| 5 | Good (3) | 4 d | 0.921 | ~10.2 | 5.14 | ~10 d |

> Approximate values — exact results depend on w[] weights.

### `GET /sessions/next` card selection priority (integration phase)

1. **Due cards** with status `integration_review` or `isolation_mastered`
2. **New encounters** (cards not yet seen in this integration round)
3. **Any non-confirmed card** as fallback

Cards with status `integration_confirmed` are excluded unless they become due via spaced repetition.

### `POST /sessions/answer` response (integration phase)

Confirmed:
```json
{
  "correct": true,
  "success_streak": 4,
  "status": "integration_confirmed",
  "next_due": "<now + 37 days>",
  "explanation": "Confirmed | Accuracy: 100.0% (Integration), Streak: 4"
}
```

Failed (not yet at 3 failures):
```json
{
  "correct": false,
  "success_streak": 0,
  "status": "integration_review",
  "next_due": "<now + 1 day>",
  "explanation": "Reviewing | Accuracy: 50.0% (Integration), Streak: 0"
}
```

---

## Step 6 — Integration Complete → Batch 2 Opens

**Trigger:** all cards in the integration set reach `integration_confirmed`.

**System does:**
- Increments `completed_integration_cycles` by 1.
- Sets `isolation_phase = True`.
- Sets `current_batch_start = 6`, `current_batch_end = 10`.
- Adds 5 new elements (positions 6–10) to `user_learning_set_items`.
- The user now studies the new batch in isolation while previously confirmed cards continue to surface via spaced repetition when due.

---

## Step 7 — Spiral Review (every 2 integration cycles)

**Trigger:** `completed_integration_cycles` reaches a multiple of 2 (i.e., after cycles 2, 4, 6, …).

**Purpose:** surface previously weak cards for targeted remediation.

**System does:**
- Selects up to 20 cards with status `integration_confirmed` that have:
  - Accuracy below 70%, **or**
  - Stability score below 1.5
- Sets their status to `spiral_review`.
- These cards are interleaved into the current session.

**Spiral card lifecycle:**

```
integration_confirmed ──► spiral_review ──► integration_confirmed (if ≥ 80% accuracy over 2 attempts)
                                        └──► spiral_review (continues)
```

**`POST /sessions/answer` response (spiral review):**

```json
{
  "correct": true,
  "success_streak": 1,
  "status": "spiral_review",
  "next_due": "<now + 1 day>",
  "explanation": "Reinforcing | Accuracy: 100.0% (Integration), Streak: 1"
}
```

After passing spiral review (≥ 80% accuracy over ≥ 2 attempts):
```json
{
  "correct": true,
  "success_streak": 2,
  "status": "integration_confirmed",
  "next_due": "<now + 6 days>",
  "explanation": "Confirmed | Accuracy: 100.0% (Integration), Streak: 2"
}
```

---

## Step 8 — Dataset Completion

**Trigger:** the last batch of the dataset passes integration.

**System responds:**
- Returns HTTP 200 with `detail` message:
  `"🎉 Congratulations! You've completed the entire dataset! All cards mastered! 🏆"`
- `UserLearningSet.status` is set to `completed`.
- All `UserElementReview` records for this dataset remain intact for long-term spaced repetition.
- Previously confirmed cards will continue surfacing when `next_due` arrives, using standard SM-2 intervals.

---

## Full Status Transition Map

```
new
 │
 ▼ (first answer)
learning
 │
 ▼ (≥3 attempts, ≥80% accuracy, ≥2 consecutive correct)
isolation_mastered
 │
 ▼ (integration phase starts, first encounter)
integration_review
 │                    \
 ▼ (1 correct attempt) ▼ (3rd failure)
integration_confirmed   learning  ──► (back through isolation_mastered)
 │
 ▼ (every 2 cycles, if weak)
spiral_review
 │
 ▼ (≥80% accuracy over ≥2 attempts)
integration_confirmed
```

---

## Error Cases

| Situation | System response |
|-----------|----------------|
| User calls `/sessions/next` with no active learning set | 404 — must call `/sessions/start` first |
| All cards in current batch are mastered but integration not complete | 200 — serves integration cards |
| Dataset fully completed | 200 with congratulations message, no more cards served |
| JWT expired | 401 Unauthorized |
| Wrong answer 3× in integration | Card sent back to `learning`, user must rebuild isolation mastery |
