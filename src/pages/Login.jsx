import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { toast } from 'react-toastify';
import RegisterModal from '../components/RegisterModal.jsx';
import './Login.css';

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isForgotPassword, setIsForgotPassword] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);

  const { login, forgotPassword } = useAuth();
  const navigate = useNavigate();

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePassword = (password) => {
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
    return passwordRegex.test(password);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!isForgotPassword) {
      if (!formData.password) {
        newErrors.password = 'Password is required';
      } else if (!validatePassword(formData.password)) {
        newErrors.password = 'Password must be at least 8 characters with 1 capital, 1 small, 1 numeric, and 1 symbol';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    
    try {
      if (isForgotPassword) {
        const result = await forgotPassword(formData.email);
        if (result.success) {
          toast.success(result.message);
          setIsForgotPassword(false);
          setFormData({ email: '', password: '' });
        } else {
          toast.error(result.error || 'Failed to send reset email');
        }
      } else {
        const result = await login(formData.email, formData.password);
        if (result.success) {
          toast.success('Login successful!');
          navigate('/home');
        } else {
          toast.error(result.error || 'Login failed');
        }
      }
    } catch (error) {
      toast.error('An error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleForgotPassword = () => {
    setIsForgotPassword(!isForgotPassword);
    setFormData({ email: '', password: '' });
    setErrors({});
  };

  return (
    <div className="login-container">
      <div className="login-left">
        <div className="login-content">
          <h1>💰 Budget Tracker</h1>
          <p>Take control of your finances with our powerful budget tracking tool</p>
          <div className="features">
            <div className="feature">
              <span className="feature-icon">📊</span>
              <span>Track income and expenses</span>
            </div>
            <div className="feature">
              <span className="feature-icon">📈</span>
              <span>Visualize your spending</span>
            </div>
            <div className="feature">
              <span className="feature-icon">🎯</span>
              <span>Set and achieve goals</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="login-right">
        <div className="login-form-container">
          <h2>{isForgotPassword ? 'Forgot Password' : 'Welcome Back'}</h2>
          <p className="login-subtitle">
            {isForgotPassword 
              ? 'Enter your email to receive a magic link' 
              : 'Sign in to your account to continue'
            }
          </p>
          
          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="Enter your email"
                className={errors.email ? 'error' : ''}
              />
              {errors.email && <span className="error-message">{errors.email}</span>}
            </div>

            {!isForgotPassword && (
              <div className="form-group">
                <label htmlFor="password">Password</label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  placeholder="Enter your password"
                  className={errors.password ? 'error' : ''}
                />
                {errors.password && <span className="error-message">{errors.password}</span>}
              </div>
            )}

            <button 
              type="submit" 
              className="login-button"
              disabled={isLoading}
            >
              {isLoading ? 'Loading...' : (isForgotPassword ? 'Send Reset Link' : 'Sign In')}
            </button>
          </form>

          <div className="login-actions">
            {!isForgotPassword ? (
              <>
                <button 
                  type="button" 
                  className="forgot-password-link"
                  onClick={toggleForgotPassword}
                >
                  Forgot Password?
                </button>
                <div className="register-section">
                  <span className="register-text">Don't have an account?</span>
                  <button 
                    type="button" 
                    className="register-link"
                    onClick={() => setShowRegisterModal(true)}
                  >
                    Register here
                  </button>
                </div>
              </>
            ) : (
              <button 
                type="button" 
                className="back-to-login-link"
                onClick={toggleForgotPassword}
              >
                Back to Login
              </button>
            )}
          </div>
        </div>
      </div>

      {showRegisterModal && (
        <RegisterModal
          onClose={() => setShowRegisterModal(false)}
          onSuccess={() => {
            toast.success('Registration successful! You can now log in.');
            setShowRegisterModal(false);
          }}
        />
      )}
    </div>
  );
};

export default Login; 