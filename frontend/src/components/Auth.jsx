import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

const Auth = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      if (isLogin) {
        // FastAPI OAuth2 requires x-www-form-urlencoded format for login
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await api.post('/auth/login', formData, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        
        localStorage.setItem('token', response.data.access_token);
        navigate('/'); // Go to chat
      } else {
        // Signup expects standard JSON
        await api.post('/auth/signup', { username, password });
        // Automatically switch to login after successful signup
        setIsLogin(true);
        setError('Signup successful! Please log in.');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred. Please try again.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-ev-bg text-ev-text transition-colors duration-300">
      <div className="w-full max-w-md p-8 rounded-2xl bg-ev-sidebar shadow-2xl border border-ev-border">
        
        <h2 className="text-3xl font-bold mb-6 text-center text-ev-text">
          {isLogin ? 'Welcome Back' : 'Create Account'}
        </h2>

        {error && (
          <div className={`p-3 mb-4 rounded-lg text-sm text-center ${error.includes('successful') ? 'bg-ev-accent/20 text-ev-accent' : 'bg-red-500/20 text-red-400'}`}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-ev-muted mb-1">Username</label>
            <input
              type="text"
              required
              className="w-full px-4 py-3 rounded-lg bg-ev-input border border-ev-border focus:outline-none focus:border-ev-accent transition-colors text-ev-text"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ev-muted mb-1">Password</label>
            <input
              type="password"
              required
              className="w-full px-4 py-3 rounded-lg bg-ev-input border border-ev-border focus:outline-none focus:border-ev-accent transition-colors text-ev-text"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            className="w-full py-3 mt-2 rounded-lg bg-ev-accent hover:bg-ev-accent-hover text-ev-bg font-bold transition-colors duration-200"
          >
            {isLogin ? 'Sign In' : 'Sign Up'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => {
              setIsLogin(!isLogin);
              setError('');
            }}
            className="text-ev-muted hover:text-ev-accent text-sm transition-colors"
          >
            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Log in"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Auth;