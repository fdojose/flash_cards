// Authentication components
// ========================

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const PasswordInput = ({ name, value, onChange, disabled, minLength, required }) => {
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <input
        type={show ? 'text' : 'password'}
        name={name}
        value={value}
        onChange={onChange}
        className="input input-bordered w-full pr-10"
        required={required}
        disabled={disabled}
        minLength={minLength}
      />
      <button
        type="button"
        onClick={() => setShow(s => !s)}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 touch-manipulation"
        tabIndex={-1}
        aria-label={show ? 'Hide password' : 'Show password'}
      >
        {show ? (
          // Eye-off icon
          <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-5 0-9-4-9-7 0-1.26.55-2.44 1.5-3.4M6.1 6.1A9.956 9.956 0 0112 5c5 0 9 4 9 7 0 1.26-.55 2.44-1.5 3.4M3 3l18 18" />
          </svg>
        ) : (
          // Eye icon
          <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274 4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        )}
      </button>
    </div>
  );
};

export const LoginForm = ({ onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(formData);
      onSuccess?.();
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  return (
    <div className="card bg-base-100 shadow-xl max-w-md mx-auto">
      <div className="card-body">
        <h2 className="card-title justify-center text-2xl mb-4">Login</h2>
        
        {error && (
          <div className="alert alert-error mb-4">
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="form-control">
            <label className="label">
              <span className="label-text">Email</span>
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="input input-bordered"
              required
              disabled={loading}
            />
          </div>

          <div className="form-control">
            <label className="label">
              <span className="label-text">Password</span>
            </label>
            <PasswordInput
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              disabled={loading}
            />
            <label className="label">
              <Link 
                to="/forgot-password" 
                className="label-text-alt link link-hover text-blue-600"
              >
                Forgot password?
              </Link>
            </label>
          </div>

          <div className="card-actions justify-end gap-2 mt-6">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="btn btn-ghost"
                disabled={loading}
              >
                Cancel
              </button>
            )}
            <button
              type="submit"
              className={`btn btn-primary ${loading ? 'loading' : ''}`}
              disabled={loading}
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export const RegisterForm = ({ onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      const { confirmPassword, ...userData } = formData;
      await register(userData);
      onSuccess?.();
    } catch (err) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  return (
    <div className="card bg-base-100 shadow-xl max-w-md mx-auto">
      <div className="card-body">
        <h2 className="card-title justify-center text-2xl mb-4">Register</h2>
        
        {error && (
          <div className="alert alert-error mb-4">
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="form-control">
            <label className="label">
              <span className="label-text">Name</span>
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="input input-bordered"
              required
              disabled={loading}
            />
          </div>

          <div className="form-control">
            <label className="label">
              <span className="label-text">Email</span>
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="input input-bordered"
              required
              disabled={loading}
            />
          </div>

          <div className="form-control">
            <label className="label">
              <span className="label-text">Password</span>
            </label>
            <PasswordInput
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              disabled={loading}
              minLength={6}
            />
          </div>

          <div className="form-control">
            <label className="label">
              <span className="label-text">Confirm Password</span>
            </label>
            <PasswordInput
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              disabled={loading}
              minLength={6}
            />
          </div>

          <div className="card-actions justify-end gap-2 mt-6">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="btn btn-ghost"
                disabled={loading}
              >
                Cancel
              </button>
            )}
            <button
              type="submit"
              className={`btn btn-primary ${loading ? 'loading' : ''}`}
              disabled={loading}
            >
              {loading ? 'Creating account...' : 'Register'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export const AuthModal = ({ isOpen, onClose, mode = 'login' }) => {
  const [currentMode, setCurrentMode] = useState(mode);

  if (!isOpen) return null;

  const handleSuccess = () => {
    onClose();
  };

  return (
    <div className="modal modal-open">
      <div className="modal-backdrop" onClick={onClose}></div>
      <div className="modal-box max-w-md">
        {currentMode === 'login' ? (
          <LoginForm onSuccess={handleSuccess} onCancel={onClose} />
        ) : (
          <RegisterForm onSuccess={handleSuccess} onCancel={onClose} />
        )}
        
        <div className="text-center mt-4">
          {currentMode === 'login' ? (
            <p className="text-sm">
              Don't have an account?{' '}
              <button
                className="link link-primary"
                onClick={() => setCurrentMode('register')}
              >
                Register here
              </button>
            </p>
          ) : (
            <p className="text-sm">
              Already have an account?{' '}
              <button
                className="link link-primary"
                onClick={() => setCurrentMode('login')}
              >
                Login here
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
