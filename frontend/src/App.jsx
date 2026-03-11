import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout';
import Home from './pages/Home';
import Learn from './pages/Learn';
import Dashboard from './pages/Dashboard';
import Progress from './pages/Progress';
import Rankings from './pages/Rankings';
import Admin from './pages/Admin';
import DatasetPractice from './pages/DatasetPractice';
import FailedCards from './pages/FailedCards';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import TestCelebration from './pages/TestCelebration';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Auth routes outside of Layout */}
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          
          {/* Main app routes with Layout */}
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="learn" element={<Learn />} />
            <Route path="learn/:datasetId" element={<Learn />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="progress" element={<Progress />} />
            <Route path="rankings" element={<Rankings />} />
            <Route path="admin" element={<Admin />} />
            <Route path="datasets/:datasetId/practice" element={<DatasetPractice />} />
            <Route path="datasets/:datasetId/failed-cards" element={<FailedCards />} />
            <Route path="test-celebration" element={<TestCelebration />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
