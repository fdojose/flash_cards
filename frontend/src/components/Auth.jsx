// Authentication components
// ========================

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';

const PasswordInput = ({ name, value, onChange, disabled, minLength, required }) => {
  const [show, setShow] = useState(false);
  const { t } = useTranslation();
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
        aria-label={show ? t('auth.hidePassword') : t('auth.showPassword')}
      >
        {show ? (
          <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-5 0-9-4-9-7 0-1.26.55-2.44 1.5-3.4M6.1 6.1A9.956 9.956 0 0112 5c5 0 9 4 9 7 0 1.26-.55 2.44-1.5 3.4M3 3l18 18" />
          </svg>
        ) : (
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
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const { t } = useTranslation();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(formData);
      onSuccess?.();
    } catch (err) {
      setError(err.message || t('auth.loginFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  return (
    <div className="card bg-base-100 shadow-xl max-w-md mx-auto">
      <div className="card-body">
        <h2 className="card-title justify-center text-2xl mb-4">{t('auth.loginTitle')}</h2>

        {error && (
          <div className="alert alert-error mb-4">
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="form-control">
            <label className="label">
              <span className="label-text">{t('auth.email')}</span>
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
              <span className="label-text">{t('auth.password')}</span>
            </label>
            <PasswordInput
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              disabled={loading}
            />
            <label className="label">
              <Link to="/forgot-password" className="label-text-alt link link-hover text-blue-600">
                {t('auth.forgotPassword')}
              </Link>
            </label>
          </div>

          <div className="card-actions justify-end gap-2 mt-6">
            {onCancel && (
              <button type="button" onClick={onCancel} className="btn btn-ghost" disabled={loading}>
                {t('common.cancel')}
              </button>
            )}
            <button
              type="submit"
              className={`btn btn-primary ${loading ? 'loading' : ''}`}
              disabled={loading}
            >
              {loading ? t('auth.loggingIn') : t('auth.loginTitle')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export const RegisterForm = ({ onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({ name: '', email: '', password: '', confirmPassword: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { register } = useAuth();
  const { t } = useTranslation();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError(t('auth.passwordsMismatch'));
      setLoading(false);
      return;
    }

    try {
      const { confirmPassword, ...userData } = formData;
      await register(userData);
      onSuccess?.();
    } catch (err) {
      setError(err.message || t('auth.registrationFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  return (
    <div className="card bg-base-100 shadow-xl max-w-md mx-auto">
      <div className="card-body">
        <h2 className="card-title justify-center text-2xl mb-4">{t('auth.registerTitle')}</h2>

        {error && (
          <div className="alert alert-error mb-4">
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="form-control">
            <label className="label">
              <span className="label-text">{t('auth.name')}</span>
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
              <span className="label-text">{t('auth.email')}</span>
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
              <span className="label-text">{t('auth.password')}</span>
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
              <span className="label-text">{t('auth.confirmPassword')}</span>
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
              <button type="button" onClick={onCancel} className="btn btn-ghost" disabled={loading}>
                {t('common.cancel')}
              </button>
            )}
            <button
              type="submit"
              className={`btn btn-primary ${loading ? 'loading' : ''}`}
              disabled={loading}
            >
              {loading ? t('auth.creatingAccount') : t('auth.registerTitle')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export const AuthModal = ({ isOpen, onClose, mode = 'login' }) => {
  const [currentMode, setCurrentMode] = useState(mode);
  const { t } = useTranslation();

  if (!isOpen) return null;

  return (
    <div className="modal modal-open">
      <div className="modal-backdrop" onClick={onClose}></div>
      <div className="modal-box max-w-md">
        {currentMode === 'login' ? (
          <LoginForm onSuccess={onClose} onCancel={onClose} />
        ) : (
          <RegisterForm onSuccess={onClose} onCancel={onClose} />
        )}

        <div className="text-center mt-4">
          {currentMode === 'login' ? (
            <p className="text-sm">
              {t('auth.noAccount')}{' '}
              <button className="link link-primary" onClick={() => setCurrentMode('register')}>
                {t('auth.registerHere')}
              </button>
            </p>
          ) : (
            <p className="text-sm">
              {t('auth.hasAccount')}{' '}
              <button className="link link-primary" onClick={() => setCurrentMode('login')}>
                {t('auth.loginHere')}
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
