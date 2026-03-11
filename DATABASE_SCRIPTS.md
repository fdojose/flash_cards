# Database Management Scripts

This directory contains scripts to manage the flashcard system database.

## Scripts Overview

### 🔄 `repopulate_db.sh` - Database Repopulation
Repopulates the database with essential data after reset/deletion without removing existing data.

**Usage:**
```bash
# Full repopulation (admin user + system configs)
./repopulate_db.sh

# Only verify current installation
./repopulate_db.sh --verify

# Only repopulate system configurations
./repopulate_db.sh --configs

# Show help
./repopulate_db.sh --help
```

**What it does:**
- ✅ Creates admin user (`admin@flashcards.com` / `admin123`)
- ✅ Adds 17 system configuration variables
- ✅ Runs database migrations (if backend is running)
- ✅ Verifies installation

### 🔥 `reset_db.sh` - Complete Database Reset
**⚠️ WARNING: This DELETES ALL existing data!**

Completely resets the database and repopulates it with fresh data.

**Usage:**
```bash
./reset_db.sh
# You will be prompted to confirm with 'YES'
```

**What it does:**
1. 🛑 Stops all Docker services
2. 🗑️ Removes `postgres_data/` directory (ALL DATA LOST)
3. 🚀 Starts services with fresh database
4. 🔄 Runs `repopulate_db.sh` automatically

## System Configurations Restored

### Learning Algorithm (7 configs)
- `initial_set_size`: 10 - Starting flashcards for new users
- `mastery_threshold`: 3 - Correct answers needed for mastery  
- `max_set_size`: 30 - Maximum flashcards in learning set
- `stage_increment`: 10 - Cards added per stage advancement
- `mid_tier_threshold`: 80 - Mid-tier optimization (16-80 cards)
- `chunk_size_progression`: "100,75,60,50" - Large dataset chunks
- `reinforcement_percentage`: 10 - Old cards included for review

### Spaced Repetition Algorithm (10 configs)
- `initial_ease`: 2.5 - SM-2 starting ease factor
- `minimum_ease`: 1.3 - Floor ease value
- `maximum_ease`: 5.0 - Ceiling ease value
- `ease_bonus`: 0.15 - Bonus for correct answers
- `ease_penalty`: 0.2 - Penalty for wrong answers
- `initial_interval`: 1 - Initial review days
- `graduation_interval`: 4 - Days to graduate from learning
- `maximum_interval`: 365 - Maximum days between reviews
- `learning_steps`: "1,10,1440" - Minutes (1min, 10min, 1day)
- `relearning_steps`: "10,1440" - Failed card steps (10min, 1day)

## Admin Access After Repopulation

- **Frontend**: http://localhost:5173
- **Admin Panel**: http://localhost:3000/admin  
- **Backend API**: http://localhost:8000
- **Admin Email**: admin@flashcards.com
- **Admin Password**: admin123

## Troubleshooting

### Container Not Running
```bash
docker-compose up -d
```

### Database Not Ready
Wait a few seconds and try again. The scripts include retry logic.

### Permission Errors
```bash
chmod +x repopulate_db.sh reset_db.sh
```

### Frontend Port Different
The frontend might run on port 3000 instead of 5173. Check the Docker logs:
```bash
docker logs flashcard_frontend
```

### Verify Installation
```bash
./repopulate_db.sh --verify
```

## Docker Compose Services

- **postgres**: PostgreSQL 15 database (port 5433)
- **backend**: FastAPI application (port 8000)
- **frontend**: React + Vite (port 5173)
- **pgadmin**: Database management tool (port 5050, optional)

## Data Persistence

- Database data: `./postgres_data/` (external mount)
- This survives container rebuilds but NOT `reset_db.sh`
