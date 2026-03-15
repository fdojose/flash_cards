import { Link, useLocation } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { AuthModal } from './Auth';

export default function Navbar() {
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState('login');
  const { user, logout, isAuthenticated, isAdmin } = useAuth();
  const userMenuRef = useRef(null);

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

  // Close user dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, []);

  // Close menus on navigation
  useEffect(() => {
    setIsMenuOpen(false);
    setUserMenuOpen(false);
  }, [location.pathname]);

  const handleLogin = () => {
    setAuthMode('login');
    setAuthModalOpen(true);
  };

  const handleRegister = () => {
    setAuthMode('register');
    setAuthModalOpen(true);
  };

  const handleLogout = async () => {
    setUserMenuOpen(false);
    setIsMenuOpen(false);
    await logout();
  };

  return (
    <nav className="navbar-custom px-4 py-3 relative">
      <div className="flex items-center justify-between max-w-7xl mx-auto w-full">

        {/* Left: hamburger + logo */}
        <div className="flex items-center">
          <button
            className="md:hidden p-3 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 mr-2 touch-manipulation"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label="Toggle menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isMenuOpen
                ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h8m-8 6h16" />
              }
            </svg>
          </button>

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

        {/* Right: user menu / auth buttons */}
        <div className="flex items-center">
          {isAuthenticated ? (
            <div className="relative" ref={userMenuRef}>
              {/* Avatar — larger touch target */}
              <button
                className="flex items-center justify-center w-10 h-10 bg-blue-600 text-white rounded-full font-bold hover:bg-blue-700 transition-colors touch-manipulation"
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                aria-label="User menu"
              >
                {user?.username?.[0]?.toUpperCase() || 'U'}
              </button>

              {/* Dropdown — click-based, works on touch */}
              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50 border border-gray-100">
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
              )}
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <button
                onClick={handleLogin}
                className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 touch-manipulation"
              >
                Login
              </button>
              <button
                onClick={handleRegister}
                className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 touch-manipulation"
              >
                Register
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Mobile menu */}
      {isMenuOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 bg-white shadow-lg border-t border-gray-200 z-40">
          <div className="px-4 py-3 space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 px-3 py-3 rounded-md text-base font-medium transition-colors touch-manipulation ${
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

            {/* User section at bottom of mobile menu */}
            {isAuthenticated ? (
              <div className="border-t border-gray-200 pt-3 mt-2">
                <div className="px-3 py-2 text-sm text-gray-500">
                  Signed in as <span className="font-medium text-gray-800">{user?.username}</span>
                  {isAdmin && <span className="ml-2 text-xs text-blue-600">Admin</span>}
                </div>
                {isAdmin && (
                  <Link
                    to="/admin"
                    className="flex items-center space-x-3 px-3 py-3 rounded-md text-base font-medium text-gray-600 hover:bg-gray-100 touch-manipulation"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    <span>⚙️</span><span>Admin</span>
                  </Link>
                )}
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center space-x-3 px-3 py-3 rounded-md text-base font-medium text-red-600 hover:bg-red-50 touch-manipulation"
                >
                  <span>🚪</span><span>Logout</span>
                </button>
              </div>
            ) : (
              <div className="border-t border-gray-200 pt-3 mt-2 flex gap-3">
                <button
                  onClick={() => { handleLogin(); setIsMenuOpen(false); }}
                  className="flex-1 py-3 text-sm font-medium text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 touch-manipulation"
                >
                  Login
                </button>
                <button
                  onClick={() => { handleRegister(); setIsMenuOpen(false); }}
                  className="flex-1 py-3 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 touch-manipulation"
                >
                  Register
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        mode={authMode}
      />
    </nav>
  );
}
