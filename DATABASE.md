# Database Reference

PostgreSQL database. All primary keys are UUID. Timestamps are `DateTime(timezone=True)`.
Connection: host `flashcard_postgres`, port `5432`, database `flashcard_db`, user `flashcard_user`.

---

## Entity Relationship Overview

```
users
  ├─ user_roles           (1:1, FK → users.id)
  ├─ password_reset_tokens (1:N, FK → users.id)
  ├─ user_learning_sets   (1:N, FK → users.id + datasets.id)
  │    └─ user_learning_set_items (1:N, FK → user_learning_sets.id + elements.id)
  ├─ user_element_reviews (1:N, FK → users.id + elements.id)
  ├─ user_field_attempts  (1:N, FK → users.id + elements.id)
  ├─ spaced_repetition_configs (1:1, FK → users.id)
  ├─ review_sessions      (1:N, FK → users.id + datasets.id)
  ├─ card_difficulties    (1:N, FK → users.id + elements.id, unique per pair)
  ├─ optimal_schedules    (1:N, FK → users.id)
  ├─ user_stats           (1:1, FK → users.id)
  ├─ dataset_progress     (1:N, FK → users.id + datasets.id, unique per pair)
  ├─ study_sessions       (1:N, FK → users.id + datasets.id)
  ├─ weekly_goals         (1:N, FK → users.id)
  ├─ learning_insights    (1:N, FK → users.id)
  ├─ user_game_stats      (1:1, FK → users.id)
  ├─ daily_stats          (1:N, FK → users.id, unique per user+date)
  ├─ user_achievements    (1:N, FK → users.id, unique per user+achievement_title)
  ├─ user_streaks         (1:1, FK → users.id)
  └─ leaderboard_scores   (1:N, FK → users.id + datasets.id, unique per user+score_type+dataset+period)

datasets
  ├─ elements             (1:N, FK → datasets.id)
  │    └─ fields          (1:N, FK → elements.id)
  │    └─ element_tags    (M:N join table → elements.id + tags.id)
  └─ tags (via element_tags)

system_configs           (global key-value config, no FK)
badge_definitions        (no FK)
```

---

## Tables

### `users`
Core user table.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `email` | VARCHAR(255) | unique, indexed |
| `name` | VARCHAR(255) | |
| `hashed_password` | TEXT | bcrypt |
| `is_active` | BOOLEAN | default true |
| `is_admin` | BOOLEAN | default false |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

---

### `user_roles`
Optional role label per user. In practice `is_admin` on `users` is the authoritative check.

| Column | Type | Notes |
|---|---|---|
| `user_id` | UUID PK, FK → users.id | CASCADE delete |
| `role` | VARCHAR(50) | `"user"`, `"admin"`, `"moderator"` |

---

### `password_reset_tokens`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | CASCADE delete |
| `token` | VARCHAR(255) | unique, indexed |
| `expires_at` | TIMESTAMPTZ | |
| `used_at` | TIMESTAMPTZ | NULL until redeemed |
| `created_at` | TIMESTAMPTZ | |

---

### `datasets`
A dataset is a named collection of learning elements (e.g. "Puntos del Meridiano del Corazón").

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `name` | VARCHAR(255) | indexed |
| `description` | TEXT | nullable |
| `is_active` | BOOLEAN | indexed; false = hidden from users |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

---

### `elements`
A single learning item inside a dataset. Content is stored in its `fields`.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `dataset_id` | UUID FK → datasets.id | CASCADE delete, indexed |
| `code` | VARCHAR(255) | optional human identifier e.g. `"C-1"`, indexed |
| `created_at` | TIMESTAMPTZ | |

---

### `fields`
Key-value pairs that make up an element. A 2-field element is a simple Q&A pair; a 7-field element is a richly described concept.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `element_id` | UUID FK → elements.id | CASCADE delete, indexed |
| `field_name` | VARCHAR(255) | e.g. `"question"`, `"answer"`, `"location"`, indexed |
| `field_value` | TEXT | the actual content |
| `field_type` | VARCHAR(50) | `"text"`, `"image"`, `"audio"`, indexed |
| `media_url` | TEXT | nullable, used when field_type ≠ text |

---

### `tags` / `element_tags`
Optional tagging system. Rarely queried in production logic.

`tags`: `id` UUID PK, `name` VARCHAR(100) unique.

`element_tags`: composite PK (`element_id` FK → elements.id, `tag_id` FK → tags.id). Both CASCADE delete.

---

### `user_learning_sets`
The join between a user and a dataset, tracking all state for the learning progression algorithm.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | CASCADE delete |
| `dataset_id` | UUID FK → datasets.id | CASCADE delete |
| `stage` | INTEGER | default 1; progressive set size (stage N = N×10 cards active) |
| `status` | VARCHAR(50) | `"active"`, `"paused"`, `"archived"`, `"completed"` |
| `mode` | VARCHAR(50) | `"progressive"`, `"fixed"` |
| `is_paused` | BOOLEAN | |
| `chunk_number` | INTEGER | current chunk index (for large datasets) |
| `total_chunks` | INTEGER | total chunks for this dataset |
| `chunk_size` | INTEGER | adaptive: starts 100, decreases 100→75→60→50 |
| `total_dataset_size` | INTEGER | total elements in dataset |
| `current_batch_start` | INTEGER | 1-based position start of current isolation batch |
| `current_batch_end` | INTEGER | 1-based position end of current isolation batch |
| `isolation_phase` | BOOLEAN | **true** = learning new batch in isolation; **false** = integration phase |
| `mastered_up_to` | INTEGER | highest position index fully mastered |
| `batch_size` | INTEGER | default 5; elements per isolation batch |
| `completed_integration_cycles` | INTEGER | count of completed integration cycles |
| `spiral_review_mode` | BOOLEAN | true when inside a spiral review session |
| `last_spiral_review` | TIMESTAMPTZ | nullable |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

---

### `user_learning_set_items`
Explicit list of which elements belong to the user's current learning set and in what order.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `learning_set_id` | UUID FK → user_learning_sets.id | CASCADE delete |
| `element_id` | UUID FK → elements.id | CASCADE delete |
| `position` | INTEGER | sort order within the set |
| `added_at` | TIMESTAMPTZ | |

---

### `user_element_reviews`
**Central progress tracking table.** One row per (user, element) pair. Drives the mastery algorithm.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | CASCADE delete |
| `element_id` | UUID FK → elements.id | CASCADE delete |
| `status` | VARCHAR(50) | see Status Lifecycle below |
| `success_streak` | INTEGER | consecutive correct answers |
| `review_count` | INTEGER | total times reviewed |
| `last_reviewed` | TIMESTAMPTZ | nullable |
| `next_due` | TIMESTAMPTZ | nullable; FSRS-computed next review date |
| `interval_days` | INTEGER | current FSRS interval |
| `ease_factor` | INTEGER | SM-2 ease × 100 (e.g. 250 = 2.5) |
| `is_difficult` | BOOLEAN | flagged as hard |
| `accuracy_percentage` | FLOAT | running accuracy 0.0–1.0 |
| `attempts_in_window` | INTEGER | attempts counted in current review window |
| `integration_confirmed` | BOOLEAN | confirmed in integration phase |
| `integration_attempts` | INTEGER | count of integration phase attempts |
| `last_integration_attempt` | TIMESTAMPTZ | nullable |
| `stability_score` | FLOAT | FSRS S parameter (days to desired retention) |
| `difficulty` | FLOAT | FSRS D parameter (1=easy, 10=hard) |
| `last_status_change` | TIMESTAMPTZ | set on every status transition |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

#### Status Lifecycle

```
new → learning → isolation_mastered → integration_review → integration_confirmed → spiral_review
                                                         ↑ (may bounce back here on failure)
```

| Status | Meaning |
|---|---|
| `new` | never attempted |
| `learning` | in active isolation practice, not yet mastered |
| `isolation_mastered` | passed isolation phase (≥ window filled, accuracy ≥ 80%, streak ≥ 2) |
| `integration_review` | promoted to integration phase; being tested alongside other cards |
| `integration_confirmed` | confirmed in integration (accuracy 100% in window of 1) |
| `spiral_review` | comprehensive spiral session card |

Mastery window size is determined by field count:
- 1 field → window 2 (`single_field_mastery_window`)
- 2 fields → window 3 (`two_field_mastery_window`)
- 3+ fields → `min(floor(field_count × 1.5), 8)` capped by `isolation_max_mastery_window`
- integration phase → window 2 (`integration_mastery_window`) — but only for already-promoted statuses; `learning`/`new` still use isolation window.

**Promotion guard**: `update_card_classification` is only called when `len(recent_attempts) >= window`. Cards with fewer total attempts stay in `learning` until the window is full.

---

### `user_field_attempts`
Granular per-answer log. Used to compute recent accuracy for the mastery window.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | CASCADE delete |
| `element_id` | UUID FK → elements.id | CASCADE delete |
| `question_field` | VARCHAR(255) | which field was shown as the question |
| `answer_field` | VARCHAR(255) | which field was being tested |
| `user_answer` | TEXT | nullable |
| `correct_answer` | TEXT | |
| `is_correct` | BOOLEAN | |
| `attempted_at` | TIMESTAMPTZ | |
| `response_time_ms` | INTEGER | nullable |

**Key query pattern** — fetch the mastery window:
```sql
SELECT * FROM user_field_attempts
WHERE user_id = :uid AND element_id = :eid
ORDER BY attempted_at DESC
LIMIT :window_size;
```

---

### `spaced_repetition_configs`
Per-user FSRS / SM-2 parameter overrides. One row per user; created on first login.

| Column | Type | Notes |
|---|---|---|
| `user_id` | UUID PK, FK → users.id | CASCADE delete |
| `algorithm` | VARCHAR(50) | `"sm2"`, `"fsrs"`, `"anki"` |
| `desired_retention` | FLOAT | target retention rate, default 0.9 |
| `initial_ease` | FLOAT | SM-2, default 2.5 |
| `minimum_ease` | FLOAT | SM-2, default 1.3 |
| `maximum_ease` | FLOAT | SM-2, default 5.0 |
| `initial_interval` | INTEGER | days, default 1 |
| `graduation_interval` | INTEGER | days, default 6 |
| `maximum_interval` | INTEGER | days, default 365 |
| `learning_steps` | VARCHAR(100) | comma-separated minutes, default `"1,10,1440"` |
| `relearning_steps` | VARCHAR(100) | comma-separated minutes, default `"10,1440"` |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

---

### `review_sessions`
Session-level summary (from spaced module). Separate from `study_sessions` in dashboard module.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | CASCADE delete |
| `dataset_id` | UUID FK → datasets.id | CASCADE delete, nullable |
| `session_type` | VARCHAR(50) | `"review"`, `"learning"`, `"cramming"` |
| `cards_reviewed` | INTEGER | |
| `cards_correct` | INTEGER | |
| `total_time_ms` | INTEGER | session duration |
| `started_at` | TIMESTAMPTZ | |
| `ended_at` | TIMESTAMPTZ | nullable |

---

### `card_difficulties`
Computed difficulty profile per (user, element). Unique constraint on pair.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | |
| `element_id` | UUID FK → elements.id | |
| `average_response_time` | FLOAT | seconds |
| `error_rate` | FLOAT | 0.0–1.0 |
| `difficulty_score` | FLOAT | 0.0–1.0 |
| `learning_velocity` | FLOAT | |
| `retention_rate` | FLOAT | |
| `first_seen` / `last_calculated` | TIMESTAMPTZ | |

---

### `optimal_schedules`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | |
| `target_retention` | FLOAT | default 0.9 |
| `daily_review_limit` | INTEGER | default 50 |
| `preferred_study_time` | VARCHAR(50) | `"morning"`, `"afternoon"`, `"evening"` |
| `next_7_days_count` | INTEGER | |
| `next_30_days_count` | INTEGER | |
| `optimal_session_length` | INTEGER | minutes |
| `updated_at` | TIMESTAMPTZ | |

---

### `user_stats`
Cached aggregate stats. One row per user (PK = user_id). Updated periodically, not always real-time.

| Column | Type | Notes |
|---|---|---|
| `user_id` | UUID PK, FK → users.id | |
| `total_elements_seen` | INTEGER | |
| `total_elements_mastered` | INTEGER | |
| `total_reviews` | INTEGER | |
| `total_study_time_minutes` | INTEGER | |
| `overall_accuracy` | FLOAT | 0–100 |
| `current_streak` | INTEGER | ⚠ not reliably written (known bug) |
| `max_streak` | INTEGER | ⚠ not reliably written (known bug) |
| `active_datasets` | INTEGER | |
| `completed_datasets` | INTEGER | |
| `avg_session_length_minutes` | FLOAT | |
| `sessions_this_week` | INTEGER | |
| `sessions_this_month` | INTEGER | |
| `mastery_rate` | FLOAT | |
| `learning_velocity` | FLOAT | |
| `retention_rate` | FLOAT | |
| `last_updated` | TIMESTAMPTZ | |

---

### `dataset_progress`
Per-user per-dataset progress snapshot. Unique on (user_id, dataset_id).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | |
| `dataset_id` | UUID FK → datasets.id | |
| `elements_in_dataset` | INTEGER | |
| `elements_seen` | INTEGER | |
| `elements_mastered` | INTEGER | |
| `current_stage` | INTEGER | |
| `accuracy_rate` | FLOAT | |
| `avg_response_time` | FLOAT | seconds |
| `total_study_time` | INTEGER | minutes |
| `status` | VARCHAR(50) | `"active"`, `"completed"`, `"paused"` |
| `completion_percentage` | FLOAT | |
| `started_at` / `last_studied` / `completed_at` | TIMESTAMPTZ | |

---

### `study_sessions`
Dashboard-level session log (separate from `review_sessions`).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | |
| `dataset_id` | UUID FK → datasets.id | nullable |
| `session_type` | VARCHAR(50) | `"review"`, `"learning"`, `"practice"` |
| `cards_studied` | INTEGER | |
| `cards_correct` | INTEGER | |
| `cards_new` | INTEGER | |
| `cards_due` | INTEGER | |
| `duration_minutes` | INTEGER | |
| `avg_response_time` | FLOAT | seconds per card |
| `accuracy_rate` | FLOAT | |
| `improvement_score` | FLOAT | |
| `device_type` | VARCHAR(50) | `"mobile"`, `"desktop"`, `"tablet"` |
| `time_of_day` | VARCHAR(20) | `"morning"`, `"afternoon"`, `"evening"`, `"night"` |
| `started_at` / `ended_at` | TIMESTAMPTZ | |

---

### `weekly_goals`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | |
| `week_start_date` | TIMESTAMPTZ | |
| `target_sessions_per_week` | INTEGER | default 5 |
| `target_minutes_per_week` | INTEGER | default 150 |
| `target_cards_per_week` | INTEGER | default 100 |
| `sessions_completed` | INTEGER | |
| `minutes_studied` | INTEGER | |
| `cards_studied` | INTEGER | |
| `goal_achieved` | BOOLEAN | |
| `streak_weeks` | INTEGER | consecutive goal-achieving weeks |
| `created_at` | TIMESTAMPTZ | |

---

### `learning_insights`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | |
| `insight_type` | VARCHAR(100) | `"performance"`, `"pattern"`, `"recommendation"` |
| `title` | VARCHAR(255) | |
| `message` | TEXT | |
| `priority` | VARCHAR(20) | `"low"`, `"medium"`, `"high"` |
| `data_points` | JSON | metadata about the analysis |
| `confidence_score` | FLOAT | 0.0–1.0 |
| `is_read` | BOOLEAN | |
| `is_actionable` | BOOLEAN | |
| `generated_at` | TIMESTAMPTZ | |
| `expires_at` | TIMESTAMPTZ | nullable |

---

### `user_game_stats`
Extended gamification stats. One row per user (unique on user_id).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | unique |
| `total_cards_answered` | INTEGER | |
| `correct_answers` | INTEGER | |
| `total_response_time_ms` | INTEGER | |
| `accuracy_percentage` | FLOAT | derived: correct/total × 100 |
| `average_response_time_ms` | INTEGER | derived |
| `cards_mastered` | INTEGER | |
| `study_streak_days` | INTEGER | |
| `total_study_sessions` | INTEGER | |
| `speed_score` | FLOAT | volume-weighted speed ranking score |
| `overall_score` | FLOAT | combined ranking score |
| `experience_points` | INTEGER | |
| `level` | INTEGER | |
| `achievements_count` | INTEGER | |
| `last_activity_date` | TIMESTAMPTZ | nullable |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

---

### `daily_stats`
One row per (user, date). Used for streak calculation.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | |
| `date` | TIMESTAMPTZ | date of activity |
| `cards_answered` | INTEGER | |
| `correct_answers` | INTEGER | |
| `study_time_minutes` | INTEGER | |
| `created_at` | TIMESTAMPTZ | |

Unique constraint: `(user_id, date)`.

---

### `user_achievements`
Badge/achievement records per user. Unique on `(user_id, achievement_title)`.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | CASCADE delete |
| `achievement_title` | VARCHAR(255) | |
| `achievement_description` | TEXT | |
| `badge_emoji` | VARCHAR(10) | |
| `date_awarded` | TIMESTAMPTZ | |

---

### `user_streaks`
One row per user (PK = user_id).

| Column | Type | Notes |
|---|---|---|
| `user_id` | UUID PK, FK → users.id | CASCADE delete |
| `current_streak` | INTEGER | |
| `max_streak` | INTEGER | |
| `last_activity` | TIMESTAMPTZ | nullable |
| `streak_type` | VARCHAR(50) | `"daily"`, `"weekly"` |
| `updated_at` | TIMESTAMPTZ | |

---

### `leaderboard_scores`
Unique on `(user_id, score_type, dataset_id, period)`.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | CASCADE delete |
| `dataset_id` | UUID FK → datasets.id | SET NULL on delete; NULL = global |
| `score_type` | VARCHAR(100) | `"mastered"`, `"streak"`, `"sessions"`, `"accuracy"` |
| `value` | INTEGER | |
| `period` | VARCHAR(50) | `"daily"`, `"weekly"`, `"monthly"`, `"all_time"` |
| `updated_at` | TIMESTAMPTZ | |

---

### `badge_definitions`
Catalog of available badges. No FK to users.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `name` | VARCHAR(255) | unique |
| `description` | TEXT | |
| `icon` | VARCHAR(10) | emoji |
| `criteria_type` | VARCHAR(100) | `"elements_mastered"`, `"streak_days"`, etc. |
| `criteria_value` | INTEGER | threshold to earn the badge |
| `is_active` | BOOLEAN | |
| `created_at` | TIMESTAMPTZ | |

---

### `system_configs`
Global key-value configuration. All algorithm thresholds live here. No FK.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `key` | VARCHAR(100) | unique, indexed |
| `value` | TEXT | always stored as string |
| `value_type` | VARCHAR(20) | `"string"`, `"integer"`, `"float"`, `"boolean"` |
| `description` | TEXT | |
| `category` | VARCHAR(50) | see below |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

#### Config Keys by Category

**`classification`** — mastery promotion thresholds:

| Key | Value | Meaning |
|---|---|---|
| `isolation_mastery_attempts_required` | 3 | global minimum attempts before classification runs |
| `isolation_mastery_accuracy_threshold` | 0.8 | accuracy required in isolation window |
| `isolation_mastery_success_streak_required` | 2 | consecutive correct answers required |
| `learning_accuracy_threshold` | 0.6 | accuracy to exit pure-learning state |
| `learning_min_attempts` | 2 | minimum attempts before exiting learning |
| `integration_confirmation_attempts_required` | 1 | attempts needed to confirm integration |
| `integration_confirmation_accuracy_threshold` | 1.0 | must be 100% to confirm |
| `allow_status_downgrading` | false | whether cards can regress |
| `track_isolation_attempts` | true | |
| `track_integration_attempts` | true | |

**`fsrs_mastery`** — dynamic mastery window sizes:

| Key | Value | Meaning |
|---|---|---|
| `single_field_mastery_window` | 2 | window for 1-field cards |
| `two_field_mastery_window` | 3 | window for 2-field cards (Q&A) |
| `isolation_field_multiplier` | 1.5 | multiplier: `floor(fields × 1.5)` |
| `isolation_min_mastery_window` | 2 | minimum window |
| `isolation_max_mastery_window` | 8 | maximum window |
| `default_mastery_window` | 3 | fallback when field count unavailable |
| `integration_mastery_window` | 2 | window for integration-phase cards |
| `required_mastery_window` | 2 | legacy; used in some queries |
| `isolation_mastery_percentage` | 0.75 | alternate accuracy threshold (some code paths) |
| `initial_stability_score` | 1.0 | starting FSRS S value |

**`fsrs_integration`** — FSRS stability mechanics:

| Key | Value | Meaning |
|---|---|---|
| `integration_enhancement_enabled` | true | master switch |
| `integration_confirmation_threshold` | 0.8 | accuracy for confirmation |
| `integration_max_attempts` | 3 | max attempts before returning to isolation |
| `stability_boost_factor` | 1.2 | S × 1.2 on success |
| `stability_decay_factor` | 0.8 | S × 0.8 on failure |
| `stability_maintenance_boost` | 1.05 | boost for confirmed cards |
| `stability_max_score` | 3.0 | cap on stability |
| `integration_failure_penalty` | 0.85 | stability penalty on failure |
| `reconsolidation_threshold` | 2 | failures before reconsolidation |

**`learning`** — set size and progression:

| Key | Value | Meaning |
|---|---|---|
| `initial_set_size` | 10 | starting active card count |
| `stage_increment` | 10 | cards added per stage advance |
| `max_set_size` | 30 | maximum active card count |
| `batch_size` | 5 | elements per isolation batch |
| `reinforcement_percentage` | 10 | % of prior cards included in new batch |
| `mastery_review_window` | 10 | recent attempts to consider (legacy) |
| `integration_mastery_percentage` | 0.7 | accuracy threshold in integration phase |
| `chunk_size_progression` | 100,75,60,50 | adaptive chunk sizes for large datasets |
| `mid_tier_threshold` | 80 | datasets 16–80 cards use mid-tier logic |

**`spiral_learning`**:

| Key | Value | Meaning |
|---|---|---|
| `spiral_learning_enabled` | true | |
| `spiral_review_trigger_interval` | 2 | integration cycles before spiral review |
| `spiral_review_max_cards` | 20 | cards per spiral session |
| `spiral_stability_threshold` | 1.5 | S below this = weak card |
| `spiral_weakness_threshold` | 0.6 | accuracy below this = weak |
| `spiral_integration_failure_weight` | 2.0 | weight multiplier for failed integration cards |

**`ranking`**:

| Key | Value | Meaning |
|---|---|---|
| `cards_answered_min_threshold` | 20 | minimum for leaderboard appearance |
| `accuracy_min_cards` | 5 | minimum for accuracy ranking |
| `speed_min_cards` | 10 | minimum for speed ranking |

---

## Common Query Patterns

**All attempts for a user on a specific dataset:**
```sql
SELECT ufa.*
FROM user_field_attempts ufa
JOIN elements e ON ufa.element_id = e.id
WHERE ufa.user_id = '<user_uuid>'
  AND e.dataset_id = '<dataset_uuid>'
ORDER BY ufa.attempted_at DESC;
```

**Card status summary for a user on a dataset:**
```sql
SELECT uer.status, COUNT(*) AS count
FROM user_element_reviews uer
JOIN user_learning_set_items ulsi ON uer.element_id = ulsi.element_id
JOIN user_learning_sets uls ON ulsi.learning_set_id = uls.id
WHERE uls.user_id = '<user_uuid>'
  AND uls.dataset_id = '<dataset_uuid>'
GROUP BY uer.status;
```

**Recent attempts for mastery window (newest first):**
```sql
SELECT * FROM user_field_attempts
WHERE user_id = '<user_uuid>' AND element_id = '<element_uuid>'
ORDER BY attempted_at DESC
LIMIT <window_size>;
```

**Cards still in learning (not yet promoted) for a user:**
```sql
SELECT e.code, uer.status, uer.review_count, uer.accuracy_percentage
FROM user_element_reviews uer
JOIN elements e ON uer.element_id = e.id
WHERE uer.user_id = '<user_uuid>'
  AND uer.status IN ('new', 'learning');
```

**Find user by email:**
```sql
SELECT * FROM users WHERE email = 'user@example.com';
```

**Count of attempts per card with accuracy:**
```sql
SELECT
  e.code,
  COUNT(*) AS total,
  SUM(CASE WHEN ufa.is_correct THEN 1 ELSE 0 END) AS correct,
  ROUND(AVG(CASE WHEN ufa.is_correct THEN 1.0 ELSE 0.0 END) * 100, 1) AS accuracy_pct
FROM user_field_attempts ufa
JOIN elements e ON ufa.element_id = e.id
WHERE ufa.user_id = '<user_uuid>'
  AND e.dataset_id = '<dataset_uuid>'
GROUP BY e.id, e.code
ORDER BY total DESC;
```

**Get a user's learning set state for a dataset:**
```sql
SELECT uls.*, d.name AS dataset_name
FROM user_learning_sets uls
JOIN datasets d ON uls.dataset_id = d.id
WHERE uls.user_id = '<user_uuid>'
  AND uls.dataset_id = '<dataset_uuid>';
```

---

## Notes on Data Integrity

- **Dual session tables**: `review_sessions` (spaced module) and `study_sessions` (dashboard module) both log session data independently. They are not linked.
- **`user_stats` is a cache**: real-time accuracy should be computed from `user_field_attempts`, not `user_stats`.
- **`UserElementReview.status`** is the authoritative card state. The `last_status_change` column is set on every transition.
- **`isolation_phase` on `user_learning_sets`** determines which mastery window to use: `true` → dynamic window based on field count; `false` → integration window (but only for cards already at `isolation_mastered` or above — `learning`/`new` cards always use the isolation window regardless).
- **`system_configs.value`** is always a TEXT string. Use `value_type` to cast: `integer` → `int()`, `float` → `float()`, `boolean` → check if value in `("true","1","yes","on")`.
