# 🧠 Flashcard Learning System - Backend

## 📋 Overview

FastAPI backend for the Flashcard Learning System. This server provides REST APIs for:

- **Authentication**: User registration, login, JWT management
- **Dataset Management**: Upload and manage learning datasets
- **Learning Sessions**: Flashcard presentation and progress tracking
- **Spaced Repetition**: Intelligent review scheduling
- **Gamification**: Badges, streaks, and leaderboards
- **Progress Dashboard**: Statistics and learning analytics

## 🛠 Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with bcrypt password hashing
- **Validation**: Pydantic schemas
- **Migrations**: Alembic
- **Testing**: pytest
- **Documentation**: Auto-generated OpenAPI/Swagger docs

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL
- Docker (optional)

### Installation

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your database and JWT settings
   ```

4. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Start the development server**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the API documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📁 Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── alembic.ini            # Alembic configuration
├── alembic/               # Database migrations
├── auth/                  # Authentication module
│   ├── __init__.py
│   ├── models.py          # User and role models
│   ├── routes.py          # Auth endpoints
│   └── schemas.py         # Pydantic schemas
├── datasets/              # Dataset management module
├── sessions/              # Learning session module
├── spaced/                # Spaced repetition module
├── gamification/          # Badges and achievements module
├── dashboard/             # Progress dashboard module
├── core/                  # Shared utilities
│   ├── database.py        # Database connection
│   ├── security.py        # JWT and password utilities
│   └── config.py          # Settings management
└── tests/                 # Test suite
```

## 🔧 Development

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/flashcard_db

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=True
API_V1_STR=/api/v1
```

### Database Setup

1. **Create PostgreSQL database**:
   ```sql
   CREATE DATABASE flashcard_db;
   CREATE USER flashcard_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE flashcard_db TO flashcard_user;
   ```

2. **Initialize Alembic** (if not already done):
   ```bash
   alembic init alembic
   ```

3. **Create and run migrations**:
   ```bash
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

### API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📡 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh JWT token

### Datasets
- `GET /datasets/` - List available datasets
- `POST /datasets/upload` - Upload new dataset (admin only)
- `GET /datasets/{dataset_id}` - Get dataset details

### Learning Sessions
- `POST /sessions/start` - Start/resume learning session
- `GET /sessions/next` - Get next flashcard question
- `POST /sessions/answer` - Submit answer and update progress
- `POST /sessions/evaluate` - Check if stage is completed

### Progress & Dashboard
- `GET /users/progress` - Get user progress statistics
- `GET /users/badges` - Get user achievements
- `GET /users/streak` - Get current study streak

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment

1. **Set environment variables for production**
2. **Use production-grade WSGI server**:
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```
3. **Set up reverse proxy** (nginx)
4. **Configure SSL certificates**
5. **Set up monitoring and logging**

## 🧪 Testing Strategy

- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test API endpoints and database interactions  
- **Performance Tests**: Load testing for critical endpoints
- **Security Tests**: Authentication and authorization testing

## 📊 Monitoring & Logging

- **Structured logging** with Loguru
- **Health check endpoints** for monitoring
- **Error tracking** with Sentry (optional)
- **Metrics collection** for performance monitoring

## 🔒 Security Features

- **Password hashing** with bcrypt
- **JWT authentication** with refresh tokens
- **CORS protection** for frontend integration
- **Rate limiting** for API abuse prevention
- **Input validation** with Pydantic schemas
- **SQL injection protection** with SQLAlchemy ORM

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes** and add tests
4. **Run tests**: `pytest`
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Create Pull Request**

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

## 🚀 Next Steps

After completing the backend setup:

1. **Implement authentication module** (Phase 2)
2. **Set up dataset management** (Phase 3)
3. **Build learning session engine** (Phase 4)
4. **Add spaced repetition logic** (Phase 5)
5. **Implement gamification features** (Phase 6)
6. **Create progress dashboard** (Phase 7)
7. **Add comprehensive testing** (Phase 8)

For more details, see the [Implementation Plan](../implementation_plan.md).
