import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setError('');
      const data = await login(email, password);
      // Let the ProtectedRoute handle redirection once user state is populated
      // Or we can manually fetch user if needed, but context handles it.
      // We wait for a bit so context can fetch user, or we decode the JWT locally.
      // For simplicity, we just redirect home for now, or to dashboard.
      // Since context fetchUser might take a moment, we can use window.location
      window.location.href = '/';
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to login');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[80vh] px-4">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md p-8 space-y-6 bg-film-card bg-opacity-50 backdrop-blur-xl border border-gray-800 rounded-2xl shadow-xl"
      >
        <div className="text-center">
          <h2 className="text-3xl font-bold text-white mb-2">Welcome Back</h2>
          <p className="text-gray-400">Sign in to your FilmInsight account</p>
        </div>

        {error && <div className="p-3 text-sm text-red-500 bg-red-500/10 rounded-lg">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
            <input 
              type="email" 
              required
              className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg focus:ring-2 focus:ring-film-accent focus:border-transparent outline-none text-white transition-all"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Password</label>
            <input 
              type="password" 
              required
              className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg focus:ring-2 focus:ring-film-accent focus:border-transparent outline-none text-white transition-all"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button 
            type="submit" 
            className="w-full py-3 px-4 bg-film-accent hover:bg-film-accent/90 text-white font-bold rounded-lg transition-colors"
          >
            Sign In
          </button>
        </form>

        <p className="text-center text-sm text-gray-400">
          Don't have an account? <Link to="/register" className="text-film-accent hover:underline">Register here</Link>
        </p>
      </motion.div>
    </div>
  );
}
