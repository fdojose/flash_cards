import { Link, useLocation } from 'react-router-dom';
import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { AuthModal } from './Auth';

export default function Navbar() {
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState('login');
  const { user, logout, isAuthenticated, isAdmin } = useAuth();

  const navItems = [
    { path: '/', name: 'Home', icon: '🏠' },
    ...(isAuthenticated ? [
      { path: '/learn', name: 'Learn', icon: '📚' },
      { path: '/dashboard', name: 'Dashboard', icon: '📊' },
      { path: '/progress', name: 'Progress', icon: '📈' },
      { path: '/rankings', name: 'Rankings', icon: '🏆' },
    ] : []),
  ];

  const isActive = (path) => location.pathname === path;

  const handleLogin = () => {
    setAuthMode('login');
    setAuthModalOpen(true);
  };

  const handleRegister = () => {
    setAuthMode('register');
    setAuthModalOpen(true);
  };

  const handleLogout = async () => {
    await logout();
  };

  return (
    <nav className="navbar-custom px-4 py-3">
      <div className="flex items-center justify-between max-w-7xl mx-auto w-full">
        {/* Mobile menu button */}
        <div className="flex items-center">
          <button
            className="md:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 mr-3"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h8m-8 6h16" />
            </svg>
          </button>

          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2 text-xl font-bold text-gray-900 hover:text-blue-600">
            <span className="text-2xl">🧠</span>
            <span>FlashLearn</span>
          </Link>
        </div>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center space-x-1">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive(item.path)
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.name}</span>
            </Link>
          ))}
        </div>

        {/* User menu */}
        <div className="flex items-center">
          {isAuthenticated ? (
            <div className="relative group">
              <button className="flex items-center justify-center w-8 h-8 bg-blue-600 text-white rounded-full text-sm font-bold hover:bg-blue-700 transition-colors">
                {user?.username?.[0]?.toUpperCase() || 'U'}
              </button>
              
              {/* Dropdown menu */}
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                <div className="px-4 py-2 text-sm text-gray-700 border-b">
                  <div className="font-medium">{user?.username}</div>
                  {isAdmin && <div className="text-xs text-blue-600">Admin</div>}
                </div>
                <Link to="/dashboard" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                  📊 Dashboard
                </Link>
                <Link to="/progress" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                  📈 Progress
                </Link>
                {isAdmin && (
                  <Link to="/admin" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                    ⚙️ Admin
                  </Link>
                )}
                <button 
                  onClick={handleLogout}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  🚪 Logout
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <button 
                onClick={handleLogin}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900"
              >
                Login
              </button>
              <button 
                onClick={handleRegister}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Register
              </button>
            </div>
          )}
        </div>

        {/* Mobile Navigation Menu */}
        {isMenuOpen && (
          <div className="absolute top-full left-0 right-0 bg-white shadow-lg border-t border-gray-200 md:hidden">
            <div className="px-4 py-2 space-y-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive(item.path)
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                  onClick={() => setIsMenuOpen(false)}
                >
                  <span>{item.icon}</span>
                  <span>{item.name}</span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>

      <AuthModal 
        isOpen={authModalOpen} 
        onClose={() => setAuthModalOpen(false)} 
        mode={authMode}
      />
    </nav>
  );
}
