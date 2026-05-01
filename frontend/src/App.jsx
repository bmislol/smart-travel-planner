import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Auth from './components/Auth';
import Chat from './components/Chat';

// A simple wrapper to protect the chat route
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// Placeholder for our Chat Interface (Phase 3)
const ChatPlaceholder = () => (
  <div className="min-h-screen flex items-center justify-center bg-ev-bg text-ev-text">
    <div className="text-center">
      <h1 className="text-4xl font-bold mb-4">You are logged in!</h1>
      <p className="text-ev-muted">Phase 3: Chat Interface coming next.</p>
      <button 
        onClick={() => { localStorage.removeItem('token'); window.location.reload(); }}
        className="mt-6 px-6 py-2 bg-ev-input hover:bg-ev-hover rounded border border-ev-border transition-colors"
      >
        Logout
      </button>
    </div>
  </div>
);

function App() {
  // Let's force the dark theme by default so it looks cool immediately
  useEffect(() => {
    document.documentElement.classList.add('theme-dark');
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Auth />} />
        <Route 
          path="/" 
          element={
            <ProtectedRoute>
              <Chat />
            </ProtectedRoute>
          } 
        />
      </Routes>
    </Router>
  );
}

export default App;