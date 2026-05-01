import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { Menu, X, Sun, Moon, Send, Plus, MessageSquare, LogOut, Loader2 } from 'lucide-react';
import api from '../api';

const Chat = () => {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isDark, setIsDark] = useState(true);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'ai', content: "Hello! I'm your Smart Travel Planner. Where would you like to go today?" }
  ]);
  
  const [recentTrips, setRecentTrips] = useState([]);
  const messagesEndRef = useRef(null);

  // Fetch chats from the database
  const fetchChats = async () => {
    try {
      const response = await api.get('/agent/chats');
      setRecentTrips(response.data);
    } catch (error) {
      console.error("Failed to fetch chats", error);
    }
  };

  // Run this once when the component loads
  useEffect(() => {
    fetchChats();
  }, []);

  // Auto-scroll to the bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(() => { scrollToBottom(); }, [messages]);

  // Theme Toggler
  const toggleTheme = () => {
    setIsDark(!isDark);
    if (isDark) {
      document.documentElement.classList.remove('theme-dark');
    } else {
      document.documentElement.classList.add('theme-dark');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const sendMessage = async (e) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      // Call our LangGraph backend!
      const response = await api.post('/agent/chat', { message: userMessage });
      
      setMessages(prev => [...prev, { role: 'ai', content: response.data.reply }]);
      
      // Refresh the sidebar so the new chat shows up instantly!
      fetchChats();
    } catch (error) {
      console.error("Chat Error:", error);
      setMessages(prev => [...prev, { 
        role: 'ai', 
        content: "*(System Error: Failed to reach the travel agent. Please check your backend connection.)*" 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-screen bg-ev-bg text-ev-text font-sans overflow-hidden transition-colors duration-300">
      
      {/* SIDEBAR */}
      <div className={`
        ${sidebarOpen ? 'w-72 translate-x-0' : 'w-0 -translate-x-full'} 
        flex-shrink-0 bg-ev-sidebar border-r border-ev-border transition-all duration-300 ease-in-out flex flex-col
      `}>
        <div className="p-4 flex items-center justify-between border-b border-ev-border">
          <button 
            onClick={() => setMessages([{ role: 'ai', content: "Starting a new journey! Where to?" }])}
            className="flex items-center gap-2 text-ev-text hover:text-ev-accent font-medium transition-colors"
          >
            <Plus size={20} /> New Trip
          </button>
          <button onClick={() => setSidebarOpen(false)} className="text-ev-muted hover:text-ev-text md:hidden">
            <X size={20} />
          </button>
        </div>
        
        {/* LIVE Database History */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          <p className="text-xs font-bold text-ev-muted uppercase tracking-wider mb-3">Recent Trips</p>
          
          {recentTrips.length === 0 ? (
            <p className="text-sm text-ev-muted italic px-2">No trips planned yet.</p>
          ) : (
            recentTrips.map((trip) => (
              <button 
                key={trip.id}
                onClick={() => {
                  // For now, this just updates the main window with the title. 
                  setMessages([
                    { role: 'user', content: trip.title },
                    { role: 'ai', content: "*(Loading full chat history requires LangGraph checkpointing!)*" }
                  ]);
                }}
                className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-ev-hover text-left transition-colors"
              >
                <MessageSquare size={16} className="text-ev-muted flex-shrink-0" />
                <span className="truncate text-sm">{trip.title.replace("I want a ", "").replace("What's the ", "")}</span>
              </button>
            ))
          )}
        </div>

        <div className="p-4 border-t border-ev-border">
          <button onClick={handleLogout} className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-ev-hover text-left transition-colors text-ev-muted hover:text-red-400">
            <LogOut size={16} />
            <span className="text-sm">Logout</span>
          </button>
        </div>
      </div>

      {/* MAIN CHAT AREA */}
      <div className="flex-1 flex flex-col min-w-0">
        
        {/* Header */}
        <header className="h-16 flex items-center justify-between px-4 border-b border-ev-border bg-ev-bg/80 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-2 -ml-2 rounded-md hover:bg-ev-hover text-ev-muted hover:text-ev-text transition-colors">
              <Menu size={20} />
            </button>
            <h1 className="font-semibold text-lg tracking-tight">Smart Travel Planner</h1>
          </div>
          <button onClick={toggleTheme} className="p-2 rounded-full hover:bg-ev-hover text-ev-muted hover:text-ev-accent transition-colors">
            {isDark ? <Sun size={20} /> : <Moon size={20} />}
          </button>
        </header>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
          <div className="max-w-3xl mx-auto space-y-8">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`
                  max-w-[85%] rounded-2xl px-5 py-4 shadow-sm
                  ${msg.role === 'user' ? 'bg-ev-input text-ev-text rounded-br-sm border border-ev-border/50' : 'bg-transparent text-ev-text'}
                `}>
                  {msg.role === 'user' ? (
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  ) : (
                    <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-ev-input prose-pre:border-ev-border">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-2 text-ev-muted bg-transparent px-5 py-4">
                  <Loader2 className="animate-spin" size={20} />
                  <span className="text-sm animate-pulse">Agent is thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Box */}
        <div className="p-4 bg-ev-bg">
          <div className="max-w-3xl mx-auto relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about a destination..."
              className="w-full bg-ev-input border border-ev-border rounded-xl pl-4 pr-12 py-4 focus:outline-none focus:border-ev-accent focus:ring-1 focus:ring-ev-accent resize-none transition-all"
              rows="1"
              style={{ minHeight: '60px', maxHeight: '200px' }}
            />
            <button 
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="absolute right-3 bottom-3 p-2 rounded-lg bg-ev-accent text-ev-bg hover:bg-ev-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={18} />
            </button>
          </div>
          <p className="text-center text-xs text-ev-muted mt-3">
            AI agents can make mistakes. Verify important travel details.
          </p>
        </div>

      </div>
    </div>
  );
};

export default Chat;