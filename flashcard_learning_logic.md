# 🧠 Flashcard Learning Progression Logic

## 🌟 Purpose

This document defines the logic and database operations behind a web-based flashcard system designed to help students **memorize structured knowledge efficiently**.

The tool is adaptable to different domains (e.g., acupuncture points, bones, car parts) and is built around the following educational goals:

- **Active recall**: Encourage retrieval practice by showing a field and asking the user to choose or recall a corresponding value.
- **Spaced repetition**: Use evidence-based review intervals to reinforce memory over time.
- **Chunked learning**: Start with a small subset (e.g., 10 elements), and progressively increase the scope (20 → 30 → 40...) only after the user demonstrates mastery.
- **Persistence**: Ensure the user’s progress and current subset are preserved between sessions.
- **Flexibility**: Allow different datasets with arbitrary fields (text, image, audio), and support customizable learning modes.

The logic below supports this through a series of PostgreSQL database tables and queries for managing:

- User learning subsets
- Stage transitions
- Review tracking
- Set archival and resets

This framework ensures learners are always working at the edge of their competence, increasing both retention and engagement over time.

---

## 🗃 Database Structure Review and Recommendations

The existing relational database structure supports all defined features with a few small additions to improve maintainability and future functionality.

### ✅ Fully Supported by Current Tables

- Multiple datasets: via `datasets` and `elements.dataset_id`
- Arbitrary fields per element: via `fields`
- User-specific active learning subsets: via `user_learning_sets`, `user_learning_set_items`
- Review tracking: via `user_element_reviews` (supports spaced repetition)
- Session-level tracking: via `user_field_attempts`
- Stage management: via `user_learning_sets.stage`
- Question-answer pairing logic: via field name/value access

### ⚠️ Recommended Additions

| Addition             | Table                                                                | Column / Change                                                        | Purpose                                            |
| -------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------------- | -------------------------------------------------- |
| Pause support        | `user_learning_sets`                                                 | `is_paused BOOLEAN DEFAULT FALSE`                                      | Allows users to suspend/resume a dataset           |
| More granular status | `user_learning_sets`                                                 | Add enum value `'paused'` to `status` (optional if using boolean flag) | Alternative to separate column                     |
| Tagging support      | new tables: `tags`, `element_tags`                                   |                                                                        | Enables thematic filtering or grouping of elements |
| Multimedia support   | `fields`                                                             | Ensure `media_url`, `field_type` are fully implemented                 | Supports image/audio-based fields                  |
| Trouble item filter  | compute or optional `is_difficult BOOLEAN` in `user_element_reviews` | Allows optimized focus mode queries                                    |                                                    |
| Dashboard stats      | new optional view/table `user_stats`                                 | Pre-aggregated stats per user                                          | Speeds up dashboard UI without repeated joins      |

You may also consider defining a `field_templates` table to enforce field type expectations per dataset.

---

# 🏅 Gamification Features (Optional Enhancements)

Adding gamification can boost user motivation and daily engagement. Here are three features you can include:

### 🎖️ Badges
- **Award badges** when users reach milestones:
  - "10 Elements Mastered"
  - "7-Day Study Streak"
  - "Completed First Dataset"
- Track via a new table `user_achievements(user_id, badge_name, date_awarded)`

### 🔥 Streak Rewards
- Count consecutive days with review activity
- Add `user_streaks(user_id, current_streak, max_streak, last_activity)`
- Visually highlight when streaks are broken or growing

### 🏆 Leaderboards
- Compare users across:
  - Total elements mastered
  - Longest streak
  - Most consistent practice (sessions per week)
- Store in `leaderboard_scores(user_id, dataset_id, score_type, value)`

### 🎨 UI Suggestions
- Show a badge shelf or streak fire icon
- Rank leaderboard with avatars and flags
- Celebrate when user earns new badge or beats previous streak

These additions are optional but powerful, especially for habit-building apps.

---

## 🧱 Revised SQL: CREATE TABLE Statements

These statements reflect the updated schema to support all current and anticipated features in the system.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE elements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    code TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    element_id UUID NOT NULL REFERENCES elements(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    field_value TEXT NOT NULL,
    field_type TEXT,        -- e.g., 'text', 'image', 'audio'
    media_url TEXT          -- Optional: URL to image/audio
);

CREATE TABLE user_learning_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    stage INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'active',  -- 'active', 'paused', 'archived'
    mode TEXT DEFAULT 'progressive',        -- or 'fixed'
    is_paused BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE user_learning_set_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    learning_set_id UUID NOT NULL REFERENCES user_learning_sets(id) ON DELETE CASCADE,
    element_id UUID NOT NULL REFERENCES elements(id) ON DELETE CASCADE,
    position INTEGER,  -- Optional ordering
    UNIQUE(learning_set_id, element_id)
);

CREATE TABLE user_element_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    element_id UUID NOT NULL REFERENCES elements(id) ON DELETE CASCADE,
    success_streak INTEGER DEFAULT 0,
    review_count INTEGER DEFAULT 0,
    last_reviewed TIMESTAMPTZ,
    next_due TIMESTAMPTZ,
    interval_days INTEGER DEFAULT 1,
    ease_factor REAL DEFAULT 2.5,
    status TEXT DEFAULT 'new',  -- 'new', 'learning', 'due', 'mastered'
    is_difficult BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, element_id)
);

CREATE TABLE user_field_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    element_id UUID NOT NULL REFERENCES elements(id) ON DELETE CASCADE,
    question_field TEXT NOT NULL,
    answer_field TEXT NOT NULL,
    correct BOOLEAN NOT NULL,
    attempted_at TIMESTAMPTZ DEFAULT now()
);

-- Optional: Tagging for elements
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE element_tags (
    element_id UUID NOT NULL REFERENCES elements(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (element_id, tag_id)
);


-- 🧾 Gamification Table Definitions

CREATE TABLE user_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_name TEXT NOT NULL,
    date_awarded TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE user_streaks (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    current_streak INTEGER DEFAULT 0,
    max_streak INTEGER DEFAULT 0,
    last_activity TIMESTAMPTZ
);

CREATE TABLE leaderboard_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dataset_id UUID REFERENCES datasets(id) ON DELETE SET NULL,
    score_type TEXT NOT NULL, -- e.g., 'mastered', 'streak', 'sessions'
    value INTEGER NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, score_type, dataset_id)
);
```

```sql
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'user',
    PRIMARY KEY (user_id)
);
```

```sql
CREATE INDEX idx_leaderboard_scores_type_dataset
ON leaderboard_scores(score_type, dataset_id, value DESC);
```
---

## 🛠 Configurable Parameters

| Parameter              | Default | Description                                    |
| ---------------------- | ------- | ---------------------------------------------- |
| Initial subset size    | 10      | How many elements are shown at the start       |
| Step size              | 10      | How many items are added after mastering a set |
| Mastery threshold      | 3       | Number of correct responses needed to master   |
| Max set size           | 50      | Optional upper limit for a growing set         |
| Review interval factor | 2.5     | Ease factor for spaced repetition              |

---

## 🧩 System Components for LLM-Based Backend Implementation

To assist an LLM-based system in generating backend code for this project, the following components and responsibilities should be defined:

### 🧱 Database Entities

- `users`: store unique identifiers, profile info.
- `datasets`: group of study elements (e.g., bones, acupuncture).
- `elements`: learning units with code and dataset\_id.
- `fields`: key-value pairs attached to elements (e.g., location, name).
- `user_learning_sets`: track a user's current subset and learning stage.
- `user_learning_set_items`: map which elements are in the user's current set.
- `user_element_reviews`: store spaced repetition data per element.
- `user_field_attempts`: optional log of specific QA attempts.

### 🧮 Backend Services

- `StartSession(user_id, dataset_id)` → initializes or resumes learning set.
- `GetCurrentSet(user_id, dataset_id)` → returns active elements.
- `SubmitAnswer(user_id, element_id, correct)` → updates review metrics.
- `EvaluateProgress(user_id, dataset_id)` → determines if mastery threshold is reached.
- `AppendNextElements(user_id, dataset_id)` → merges new 10 elements.
- `ResetSet(user_id, dataset_id)` → archives current set and starts fresh.

### 📊 Business Rules for LLM

- Mastery requires: `success_streak >= Mastery threshold` for all items.
- Add new elements only if no duplicates exist in the current set.
- Spaced repetition must update `interval_days`, `next_due`, and `ease_factor`.
- Prevent the set from growing past `Max set size`.

### 🛠 LLM Prompt Tip

Use schema introspection and state-based logic to guide flow:

> "Based on the current stage, success streaks, and next\_due values, decide whether to promote the user to the next stage or continue reviewing."

---

## 👣 User Journey

This section describes the typical user experience when interacting with the flashcard system — from starting a new dataset to mastering its contents using progressive learning and spaced repetition.

---

### 📽️ 1. Choose a Dataset

**User does:**

- Logs in or opens the app.
- Chooses a dataset to study (e.g., "Acupuncture Points", "Car Parts").

**System does:**

- Checks if there is an `active` learning set for this user and dataset.
  - If yes, loads current learning subset.
  - If no, creates a new learning set with 10 random elements and sets `stage = 1`.

---

### 🎓 2. Begin a Study Session

**User does:**

- Starts answering flashcard questions based on selected field pairings (e.g., "Show Chinese Name → Guess Location").
- Receives feedback on correct or incorrect answers.

**System does:**

- Loads all elements from the current learning set (`user_learning_set_items`).
- Tracks each attempt in `user_field_attempts`.
- Updates spaced repetition metrics in `user_element_reviews`:
  - `review_count`, `success_streak`, `last_reviewed`, `next_due`, `ease_factor`.

---

### 📈 3. Master the Current Set

**User does:**

- Continues practicing until they get all questions in the current set correct over multiple rounds.

**System does:**

- Checks for mastery:
  - Each element in the set has `success_streak >= 3` and `next_due` at least 2 days in the future.
- When mastered:
  - Appends 10 new elements to the current set.
  - Increments the learning `stage` (e.g., from 1 → 2 → 3).
  - Preserves previously learned items for review.

---

### 🔄 4. Repeat: Learn + Merge

**User does:**

- Keeps studying as the set grows: 10 → 20 → 30...
- Faces increasing challenge as older and newer elements mix.

**System does:**

- Continues to select new unseen elements from the dataset.
- Continues to track review intervals per item (adaptive review).

---

### 🏁 5. Complete or Reset the Learning Set

**User may:**

- Complete the dataset.
- Choose to stop at a certain stage (e.g., after mastering 50 elements).
- Reset the set to start over.
- Switch to another dataset.

**System can:**

- Mark the set as `archived`.
- Optionally clean up items.
- Create a fresh new set if the user requests it.
- Retain `user_element_reviews` to inform future sessions (long-term spaced repetition memory).

---

### 🔄 Spaced Repetition Logic

For each reviewed item:

- **If correct:**
  - Increase `success_streak`
  - `interval_days = interval_days * ease_factor`
  - `next_due = NOW() + interval_days`
- **If incorrect:**
  - Reset `success_streak = 0`
  - Set `interval_days = 1`, and reduce `ease_factor`

This ensures that frequently recalled items are reviewed less often, while harder items resurface more frequently.

---

### 🔐 Authentication & Security

- All `/user/...` endpoints should validate JWTs.
- Role-based access control should be enforced:
  - Protect `/user/badge` with admin-only role.
- Optional: define a `user_roles` table.
---
## 🔀 Evaluation Triggers

- After each session or round, system checks:
  - Has every element in the set been reviewed?
  - Are all `success_streak` values above the mastery threshold?
- If yes:
  - Append 10 more items from the dataset (not in set)
  - Update `stage += 1`

---

## 📡 REST API Overview

Define endpoints that allow the frontend or external services to interact with the backend logic described above.

### POST /start-session

Start or resume a learning session.

```json
Request: { "user_id": "...", "dataset_id": "..." }
Response: { "learning_set_id": "...", "stage": 1, "items": [...] }
```

### GET /current-set

Get all items in the current learning subset.

```json
Request: { "user_id": "...", "dataset_id": "..." }
Response: { "items": [ { "element_id": "...", "fields": {...} }, ... ] }
```

### POST /submit-answer

Submit an answer for review tracking.

```json
Request: { "user_id": "...", "element_id": "...", "correct": true }
Response: { "updated_review": {...}, "next_due": "..." }
```

### POST /evaluate-progress

Check whether the current set is mastered.

```json
Request: { "user_id": "...", "dataset_id": "..." }
Response: { "stage_completed": true, "new_items_added": 10 }
```

### POST /reset

Reset the current learning set.

```json
Request: { "user_id": "...", "dataset_id": "..." }
Response: { "new_learning_set_id": "..." }
```

### GET /progress

Return progress dashboard.

```json
Response: {
  "stage": 2,
  "mastered": 15,
  "due": 5,
  "total_attempts": 58,
  "trouble_items": ["element_id1", "element_id2"]
}

## 🔗 Gamification API Endpoints

To expose gamification features to the frontend:

### GET /user/badges

Returns all badges earned by the user.

```json
Response: [
  { "badge_name": "10 Elements Mastered", "date_awarded": "2025-08-03" },
  { "badge_name": "7-Day Streak", "date_awarded": "2025-08-10" }
]
```

### GET /user/streak

Returns current and max streak data.

```json
Response: {
  "current_streak": 6,
  "max_streak": 9,
  "last_activity": "2025-08-31"
}
```

### GET /leaderboard?type=mastered&dataset\_id=abc123

Returns the top ranked users by score type.

```json
Response: [
  { "user_id": "u1", "value": 92 },
  { "user_id": "u2", "value": 85 },
  { "user_id": "u3", "value": 79 }
]
```

### POST /user/badge

Optional: trigger manual badge award (admin/dev only)

```json
Request: { "user_id": "...", "badge_name": "..." }
```

These endpoints can be secured with user auth and exposed as part of the broader dashboard features.

To update gamification data at session close:

#### POST /user/streak/update

```json
Request: { "user_id": "...", "activity_date": "2025-09-01" }
```

#### POST /user/score/update

```json
Request: {
  "user_id": "...",
  "dataset_id": "...",
  "score_type": "mastered",
  "value": 84
}
```

---

## 🎨 Frontend Behavior Guidelines

To reinforce learning and user engagement:

- Use **stars** or icons to visualize `success_streak`
- Highlight **due items** in orange or red
- Show **correct answer and explanation** when the user gets it wrong
- Allow toggling between learning modes: focus, full review, fixed-cycle

---

## 🧪 Testing Matrix (LLM or QA Engineer Guidance)

| Scenario                                  | Expected Outcome                                                        |
| ----------------------------------------- | ----------------------------------------------------------------------- |
| User completes stage 1                    | System appends 10 new items, sets `stage = 2`                           |
| User fails an item 2×                     | `success_streak = 0`, item stays in set, may mark `is_difficult = true` |
| User reviews mastered item after interval | System loads it if `next_due <= today`                                  |
| User pauses a dataset                     | Dataset is excluded from session loading                                |
| User resets set manually                  | Old set archived, new one created with 10 items                         |

---

## 🎨 UI/UX Specifics (Cross-Phase Guidance)

**📌 Objective**: Ensure consistent, usable, mobile-friendly frontend implementation using React + Tailwind + DaisyUI.

### 💡 Core UI Component Specifications
- Flashcard view (question, 4 options, feedback on selection)
- Dataset selector dropdown
- Dashboard progress widgets (progress ring, bar chart)
- Badge / leaderboard modals
- Navbar with icon-based navigation

### 🧠 State Management
- Use React Context for global state (auth, active session)
- Flashcard session state stored in local `useState` or `useReducer`
- Store JWT in secure `HttpOnly` cookies (if possible), or localStorage as fallback

### 🌐 Routing Structure
- `/` – Home
- `/login`, `/register`
- `/learn/:dataset_id`
- `/dashboard`
- `/admin` (for future dataset management)

### 🛡️ Form Validation
- Use `react-hook-form` for all forms (login, dataset upload)
- Client-side validation rules + server-side fallback

---

## 🔐 Security Considerations (Cross-Phase Requirements)

**📌 Objective**: Ensure user data is protected and server endpoints are resilient.

### 🔑 Password Hashing
- Use `passlib` or `bcrypt` in FastAPI backend for hashing passwords at registration and verifying on login.

### 🔄 JWT Refresh Strategy
- Issue both access and refresh tokens
- Store refresh token securely and implement `/token/refresh` endpoint to renew short-lived JWTs

### 🌍 CORS Configuration
- Use FastAPI’s `CORSMiddleware`
- Restrict origins to production frontend domain only
- Allow credentials if using cookies

### 🚦 Rate Limiting
- Optional: Add `slowapi` or similar to restrict login attempts, API abuse
- Define burst rate (e.g., 10 req/min) and sustained rate (e.g., 100 req/hr) per IP


## 💪 User Options

These features describe what the backend should support so that the user interface can enable richer learning control and personalization.

### Backend Support for User Options

1. **Pause or resume a dataset**

   - Add a `paused` flag to `user_learning_sets`.
   - Backend logic must skip paused sets when resuming sessions.

2. \*\*Focus mode: review only items with \*\*\`\`

   - Add an optional mode filter in the flashcard selection query.
   - Could be toggled via user preferences or session settings.

3. **Manual reset of the current learning set**

   - Expose endpoint: `POST /learning-set/reset`
   - Archives current set, deletes its items, and creates a fresh 10.

4. **Switch between "progressive" and "fixed-size" learning modes**

   - Add a `mode` column to `user_learning_sets` with values: `progressive`, `fixed`.
   - Logic in `EvaluateProgress()` must check this before appending new items.

5. **Enable visual dashboard for progress**

   - Provide endpoint: `GET /progress` returning:
     - current stage, mastered count, due cards, streak distribution
     - trouble items: elements with repeated failures

---

- Pause or resume a dataset
- Focus mode: review only items with `success_streak < 2`
- Manual reset of the current learning set
- Switch between "progressive" and "fixed-size" learning modes
- Enable visual dashboard for progress

---
## 📊 User Progress Statistics

To support transparent learning and motivation, the system should compute and expose clear statistics about a user's progress.

### Suggested Stats
- **Total reviewed elements**: number of unique elements the user has seen.
- **Current stage**: the learning set stage (10 → 20 → 30...).
- **Mastered elements**: count of elements where `success_streak ≥ mastery threshold`.
- **Due elements**: number of items where `next_due ≤ NOW()`.
- **Trouble items**: items where `success_streak = 0` or `is_difficult = true`.
- **Average success streak**: average number of consecutive successes across all reviewed elements.
- **Last activity date**: time of most recent interaction.

### Recommended Query Sources
- From `user_element_reviews`:
  - Aggregate success streaks, `next_due`, and flags.
- From `user_field_attempts`:
  - Count total attempts and accuracy trends.
- From `user_learning_sets`:
  - Current stage, status, mode, pause flag.

### Frontend Suggestions
- Display as a dashboard panel.
- Use visualizations: bars, pie charts, timeline.
- Offer encouragement: e.g., "You’ve mastered 70% of your current set!"


## 🧱 Full Stack Architecture

This section summarizes the recommended full technology stack for implementing the flashcard learning system.

### 🖼️ Frontend
| Layer         | Technology            | Why |
|---------------|------------------------|-----|
| UI Framework  | **React**              | Best for dynamic UI, reusable components |
| Styling       | **Tailwind CSS**       | Utility-first, responsive, mobile-friendly |
| Components    | **DaisyUI**            | Prebuilt themes and widgets, good mobile UX |
| State mgmt    | (Optional: Zustand)    | Lightweight React state if needed |
| Build tools   | Vite or Create React App | Fast and flexible tooling |

### 🧠 Backend
| Layer           | Technology          | Why |
|------------------|----------------------|-----|
| Web framework     | **FastAPI**          | Async, fast, OpenAPI built-in, great for APIs |
| Language          | **Python 3.11+**     | Readable, compatible with ML if needed later |
| Database          | **PostgreSQL**       | Scalable, relational, and already designed for your model |
| ORM / DB access   | **SQLAlchemy** or **asyncpg** | SQLAlchemy if you prefer ORM; asyncpg if you're going fully async |
| Auth              | **JWT**              | Stateless, easy to integrate, frontend-friendly |
| Deployment        | **Docker + VPS**     | Full control for self-hosting, or use Fly.io / Render |

### ✅ Why This Stack?
- Mobile-first, responsive, clean design (React + Tailwind + DaisyUI)
- Structured and scalable logic (FastAPI + PostgreSQL)
- Full self-hosting capability
- Excellent fit for progressive learning, spaced repetition, and user dashboards


🚀 Implementation Plan

🗂️ Phase 1: Project Setup & Foundations
