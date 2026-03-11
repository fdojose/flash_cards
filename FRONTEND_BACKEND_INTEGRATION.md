# 🚀 Frontend-Backend Integration - Quick Start Guide
# ===================================================

## 📋 What We've Accomplished

✅ **API Service Layer** - Complete HTTP client for backend communication
✅ **Authentication System** - Login/register with JWT token management  
✅ **React Context** - Global auth state management
✅ **Custom Hooks** - Data fetching and state management
✅ **Connected Components** - Real UI components using backend data
✅ **Environment Configuration** - Development and production configs

---

## 🔌 Integration Components

### 1. **API Service** (`src/services/api.js`)
- HTTP client with authentication headers
- Error handling and token management
- All backend endpoints covered
- File upload support

### 2. **Authentication Context** (`src/contexts/AuthContext.jsx`)
- Global user state management
- Login/logout functionality
- Token persistence
- Auth state checking

### 3. **Custom Hooks** (`src/hooks/useApi.js`)
- `useDatasets()` - Dataset management
- `useDashboard()` - User progress data
- `useSession()` - Learning session management
- `useApi()` - Generic API calls

### 4. **Updated Components**
- **Navbar** - Login/logout with user menu
- **Home** - Real datasets from backend
- **Learn** - Interactive flashcard sessions
- **Dashboard** - Real user progress data

---

## 🏃‍♂️ Quick Start Instructions

### Option 1: Manual Development Start

```bash
# Terminal 1: Start Backend
cd backend
source ../venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Frontend  
cd frontend
npm install
npm run dev

# Terminal 3: Test Integration
cd ..
python test_integration.py
```

### Option 2: Automated Development Start

```bash
# Use our development deployment script
./deploy-dev.sh
```

---

## 🌐 Access Points

Once both services are running:

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **API Documentation**: http://localhost:8000/docs
- **Development Proxy**: http://localhost:8080 (via deploy-dev.sh)

---

## 🧪 Testing the Integration

1. **Visit the Frontend**: http://localhost:3000
2. **Register a New User**: Click "Register" in the navbar
3. **Login**: Use your credentials to log in
4. **Upload a Dataset**: Use the admin interface (if admin user)
5. **Start Learning**: Select a dataset and begin a session
6. **View Dashboard**: Check your progress and statistics

---

## 🔧 Configuration

### Backend Environment (`.env`)
```env
DATABASE_URL=postgresql://user:password@localhost/flashcard_db
SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Frontend Environment (`.env.development`)
```env
VITE_API_URL=http://localhost:8000/api
VITE_ENVIRONMENT=development
```

---

## 🌟 Key Features Now Working

### 🔐 **Authentication**
- User registration and login
- JWT token management
- Protected routes and components
- Admin role checking

### 📚 **Dataset Management**
- View available datasets
- Upload new datasets (admin)
- Dataset metadata and statistics
- Search and filtering

### 🎓 **Learning Sessions**
- Start interactive sessions
- Multiple choice questions
- Progress tracking
- Session completion stats

### 📊 **Dashboard & Progress**
- User statistics display
- Learning progress visualization
- Recent activity tracking
- Achievement system (ready)

### 🎨 **UI/UX**
- Responsive design
- Loading states
- Error handling
- Smooth transitions

---

## 🐛 Troubleshooting

### Backend Issues
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check API documentation
open http://localhost:8000/docs
```

### Frontend Issues
```bash
# Check if frontend is running
curl http://localhost:3000

# Check console for errors
# Open browser dev tools and check Console/Network tabs
```

### CORS Issues
- Ensure `CORS_ORIGINS` includes `http://localhost:3000`
- Check browser network tab for CORS errors
- Verify backend is accepting OPTIONS requests

### Authentication Issues
- Check JWT token in browser localStorage
- Verify secret key matches between environments
- Check token expiration settings

---

## 📈 Next Steps

### Immediate Testing
1. Test user registration and login
2. Upload a sample dataset
3. Start a learning session
4. Check dashboard statistics

### Future Enhancements
1. **Real-time features** with WebSockets
2. **Advanced analytics** with charts
3. **Social features** like leaderboards
4. **Mobile app** with PWA
5. **AI tutoring** integration

---

## 🎉 Success Indicators

✅ User can register and login  
✅ Datasets load from backend  
✅ Learning sessions work interactively  
✅ Dashboard shows real progress data  
✅ Navigation reflects auth state  
✅ Error handling works gracefully  

**🚀 Your Flashcard Learning System is now fully integrated and ready for users!**
