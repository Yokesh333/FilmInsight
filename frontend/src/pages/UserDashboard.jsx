import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, Image as ImageIcon, MessageSquare, Film, 
  Trash2, Calendar, Heart, User as UserIcon, Settings, 
  LogOut, Clock, LayoutDashboard, Menu, X, ArrowRight 
} from 'lucide-react';
import axios from 'axios';
import { chatAPI, favoritesAPI, recentAPI, userAPI } from '../services/api';
import MovieCard from '../components/MovieCard';

export default function UserDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview'); // overview, favorites, requests, history, profile, settings
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Data States
  const [requests, setRequests] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [recentMovies, setRecentMovies] = useState([]);
  
  // UI States
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  
  // Search / Request States
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);
  
  // Profile Form States
  const [profileForm, setProfileForm] = useState({ username: '', email: '' });

  useEffect(() => {
    if (user) {
        setProfileForm({ username: user.username, email: user.email });
    }
    
    const fetchAllData = async () => {
        try {
            const [reqRes, chatRes, favRes, recentRes] = await Promise.all([
                axios.get('/api/requests'),
                chatAPI.getHistory(''),
                favoritesAPI.getFavorites(),
                recentAPI.getRecent()
            ]);
            setRequests(reqRes.data);
            setChatHistory(chatRes);
            setFavorites(favRes);
            setRecentMovies(recentRes);
        } catch (err) {
            console.error("Failed to load dashboard data", err);
        } finally {
            setLoading(false);
        }
    };
    fetchAllData();

    const handleClickOutside = (event) => {
        if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
            setShowDropdown(false);
        }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [user]);

  // Request Search Debounce
  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      if (searchQuery.trim().length > 1 && showDropdown) {
        setIsSearching(true);
        axios.get(`/api/movie/search?query=${encodeURIComponent(searchQuery)}`)
            .then(res => setSearchResults(res.data.results || []))
            .catch(err => console.error(err))
            .finally(() => setIsSearching(false));
      } else {
        setSearchResults([]);
      }
    }, 400);
    return () => clearTimeout(delayDebounce);
  }, [searchQuery, showDropdown]);

  const handleRequestSubmit = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    try {
      await axios.post('/api/requests', { title: searchQuery.trim() });
      setMessage('Request submitted successfully!');
      setSearchQuery('');
      setShowDropdown(false);
      const res = await axios.get('/api/requests');
      setRequests(res.data);
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setMessage('Failed to submit request.');
    }
  };

  const handleRemoveFavorite = async (movieTitle) => {
    try {
      await favoritesAPI.removeFavorite(movieTitle);
      setFavorites(favorites.filter(f => f.movie_title !== movieTitle));
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteHistory = async (id) => {
    if(!window.confirm("Delete this conversation?")) return;
    try {
      await chatAPI.clearHistory(id);
      setChatHistory(chatHistory.filter(c => c.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    try {
        await userAPI.updateProfile(profileForm);
        setMessage('Profile updated successfully!');
        setTimeout(() => setMessage(''), 3000);
    } catch (err) {
        setMessage(err.response?.data?.detail || 'Failed to update profile.');
    }
  };

  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'recent', label: 'Recently Viewed', icon: Clock },
    { id: 'favorites', label: 'Favorites', icon: Heart },
    { id: 'history', label: 'Chat History', icon: MessageSquare },
    { id: 'requests', label: 'Movie Requests', icon: Film },
    { id: 'profile', label: 'Profile', icon: UserIcon },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  if (loading) {
      return (
          <div className="min-h-screen flex items-center justify-center bg-film-bg">
              <div className="w-8 h-8 border-4 border-film-accent border-t-transparent rounded-full animate-spin"></div>
          </div>
      );
  }

  return (
    <div className="min-h-screen bg-film-bg pt-20 pb-12">
      <div className="container mx-auto px-4 max-w-7xl">
        
        {/* Mobile Menu Toggle */}
        <div className="md:hidden flex justify-between items-center mb-6 bg-film-card p-4 rounded-xl border border-white/5">
            <h2 className="text-xl font-bold text-white capitalize">{activeTab.replace('-', ' ')}</h2>
            <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="text-white">
                {isMobileMenuOpen ? <X /> : <Menu />}
            </button>
        </div>

        <div className="flex flex-col md:flex-row gap-8">
          
          {/* Sidebar Navigation */}
          <motion.aside 
            initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
            className={`${isMobileMenuOpen ? 'flex' : 'hidden'} md:flex flex-col w-full md:w-64 shrink-0 bg-film-card p-6 rounded-2xl border border-white/5 h-fit sticky top-24 z-20`}
          >
            <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 bg-red-gradient rounded-full flex items-center justify-center text-xl font-bold text-white shadow-button">
                    {user?.username?.[0]?.toUpperCase()}
                </div>
                <div>
                    <h3 className="text-white font-bold">{user?.username}</h3>
                    <p className="text-xs text-gray-400 capitalize">{user?.role}</p>
                </div>
            </div>

            <nav className="flex flex-col gap-1.5">
              {navItems.map(item => (
                <button
                  key={item.id}
                  onClick={() => { setActiveTab(item.id); setIsMobileMenuOpen(false); }}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                    activeTab === item.id 
                    ? 'bg-film-accent/20 text-film-accent border border-film-accent/30' 
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  <item.icon size={18} />
                  {item.label}
                </button>
              ))}
              
              <div className="h-px bg-white/5 my-4"></div>
              
              <button
                  onClick={logout}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-red-400 hover:bg-red-500/10 transition-all"
              >
                  <LogOut size={18} />
                  Sign Out
              </button>
            </nav>
          </motion.aside>

          {/* Main Content Area */}
          <main className="flex-1 min-w-0">
            <motion.div 
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              className="bg-film-card p-6 md:p-10 rounded-2xl border border-white/5 min-h-[75vh] shadow-2xl relative overflow-hidden"
            >
              {/* Background Glow */}
              <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-film-accent/5 rounded-full blur-[120px] pointer-events-none -translate-y-1/2 translate-x-1/3"></div>

              <AnimatePresence mode="wait">
                
                {/* ── OVERVIEW TAB ─────────────────────────────────────────── */}
                {activeTab === 'overview' && (
                  <motion.div key="overview" initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}}>
                    <h2 className="text-3xl font-display font-bold text-white mb-2">Welcome back, {user?.username}</h2>
                    <p className="text-gray-400 mb-10">Here's what's happening with your FilmInsight account.</p>

                    {/* Stats Row */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
                        <div className="bg-gray-900/50 border border-white/5 p-5 rounded-2xl">
                            <h4 className="text-gray-400 text-sm font-medium mb-1">Chats</h4>
                            <p className="text-3xl font-bold text-white">{chatHistory.length}</p>
                        </div>
                        <div className="bg-gray-900/50 border border-white/5 p-5 rounded-2xl">
                            <h4 className="text-gray-400 text-sm font-medium mb-1">Favorites</h4>
                            <p className="text-3xl font-bold text-white">{favorites.length}</p>
                        </div>
                        <div className="bg-gray-900/50 border border-white/5 p-5 rounded-2xl">
                            <h4 className="text-gray-400 text-sm font-medium mb-1">Requests</h4>
                            <p className="text-3xl font-bold text-white">{requests.length}</p>
                        </div>
                        <div className="bg-gray-900/50 border border-white/5 p-5 rounded-2xl">
                            <h4 className="text-gray-400 text-sm font-medium mb-1">Viewed</h4>
                            <p className="text-3xl font-bold text-white">{recentMovies.length}</p>
                        </div>
                    </div>

                    {/* Recently Viewed Preview */}
                    <div className="mb-10">
                        <div className="flex justify-between items-end mb-6">
                            <h3 className="text-xl font-bold text-white flex items-center gap-2"><Clock className="text-film-accent"/> Recently Viewed</h3>
                            <button onClick={() => setActiveTab('recent')} className="text-sm text-gray-400 hover:text-white flex items-center gap-1">View All <ArrowRight size={14}/></button>
                        </div>
                        {recentMovies.length === 0 ? (
                            <div className="p-8 bg-gray-900/50 border border-white/5 rounded-2xl text-center text-gray-500">No recent movies. Explore our library!</div>
                        ) : (
                            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-4">
                                {recentMovies.slice(0, 5).map(m => (
                                    <MovieCard key={m.id} movie={{title: m.movie_title, poster: m.poster_url, year: m.movie_year}} onClick={() => navigate(`/chat?q=Tell me about "${m.movie_title}"`)} />
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Recent Chats Preview */}
                    <div>
                        <div className="flex justify-between items-end mb-6">
                            <h3 className="text-xl font-bold text-white flex items-center gap-2"><MessageSquare className="text-film-accent"/> Recent Chats</h3>
                            <button onClick={() => setActiveTab('history')} className="text-sm text-gray-400 hover:text-white flex items-center gap-1">View All <ArrowRight size={14}/></button>
                        </div>
                        <div className="space-y-3">
                            {chatHistory.slice(0, 3).map(chat => (
                                <div key={chat.id} className="bg-gray-900/50 border border-white/5 p-4 rounded-xl flex items-center gap-4">
                                    <div className="w-10 h-10 bg-film-accent/20 rounded-lg flex items-center justify-center shrink-0">
                                        <Film className="text-film-accent" size={20} />
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <h4 className="text-white font-medium truncate">{chat.question}</h4>
                                        <p className="text-gray-500 text-sm">{new Date(chat.timestamp).toLocaleDateString()}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                  </motion.div>
                )}

                {/* ── RECENT TAB ─────────────────────────────────────────────── */}
                {activeTab === 'recent' && (
                  <motion.div key="recent" initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}}>
                    <h2 className="text-3xl font-display font-bold text-white mb-2">Recently Viewed</h2>
                    <p className="text-gray-400 mb-8">Movies you've interacted with recently.</p>
                    
                    {recentMovies.length === 0 ? (
                        <div className="text-center py-20">
                            <Clock className="mx-auto text-gray-700 mb-4" size={64} />
                            <p className="text-gray-400 text-lg">No viewing history yet.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
                            {recentMovies.map(m => (
                                <MovieCard 
                                    key={m.id} 
                                    movie={{title: m.movie_title, poster: m.poster_url, year: m.movie_year}} 
                                    onClick={() => navigate(`/chat?q=Tell me about "${m.movie_title}"`)} 
                                />
                            ))}
                        </div>
                    )}
                  </motion.div>
                )}

                {/* ── FAVORITES TAB ──────────────────────────────────────────── */}
                {activeTab === 'favorites' && (
                  <motion.div key="favorites" initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}}>
                    <h2 className="text-3xl font-display font-bold text-white mb-2">Favorite Movies</h2>
                    <p className="text-gray-400 mb-8">Your personal collection of saved masterpieces.</p>
                    
                    {favorites.length === 0 ? (
                        <div className="text-center py-20">
                            <Heart className="mx-auto text-gray-700 mb-4" size={64} />
                            <p className="text-gray-400 text-lg">You haven't saved any movies yet.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
                            {favorites.map(fav => (
                                <MovieCard
                                  key={fav.id}
                                  movie={{title: fav.movie_title, poster: fav.poster_url, year: fav.movie_year}}
                                  isFavorite={true}
                                  onToggleFavorite={() => handleRemoveFavorite(fav.movie_title)}
                                  onClick={() => navigate(`/chat?q=Tell me about "${fav.movie_title}"`)}
                                />
                            ))}
                        </div>
                    )}
                  </motion.div>
                )}

                {/* ── REQUESTS TAB ───────────────────────────────────────────── */}
                {activeTab === 'requests' && (
                  <motion.div key="requests" initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}}>
                    <h2 className="text-3xl font-display font-bold text-white mb-2">Request a Script</h2>
                    <p className="text-gray-400 mb-8">Search TMDb to request a screenplay addition to our AI brain.</p>
                    
                    <form onSubmit={handleRequestSubmit} className="mb-10 relative z-30" ref={dropdownRef}>
                        <div className="flex flex-col sm:flex-row gap-4">
                            <div className="relative flex-1">
                                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                                <input 
                                    type="text" 
                                    className="w-full bg-gray-900 border border-white/10 rounded-xl pl-12 pr-4 py-4 text-white outline-none focus:border-film-accent shadow-inner transition-colors"
                                    placeholder="Search for a movie..."
                                    value={searchQuery}
                                    onChange={(e) => { setSearchQuery(e.target.value); setShowDropdown(true); }}
                                    onFocus={() => setShowDropdown(true)}
                                />
                            </div>
                            <button 
                                type="submit" 
                                disabled={!searchQuery.trim()}
                                className="bg-red-gradient text-white px-10 py-4 rounded-xl hover:shadow-[0_0_20px_rgba(229,9,20,0.4)] transition-all font-bold disabled:opacity-50"
                            >
                                Submit Request
                            </button>
                        </div>

                        {/* Dropdown */}
                        <AnimatePresence>
                            {showDropdown && searchQuery.trim().length > 1 && (
                                <motion.div 
                                    initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
                                    className="absolute w-full mt-2 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl max-h-80 overflow-y-auto"
                                >
                                    {isSearching ? (
                                        <div className="p-6 text-center text-gray-400">Searching TMDb...</div>
                                    ) : searchResults.length > 0 ? (
                                        <ul className="py-2">
                                            {searchResults.map((movie) => (
                                                <li key={movie.id} onClick={() => { setSearchQuery(movie.title); setShowDropdown(false); }} className="flex items-center gap-4 px-4 py-3 hover:bg-white/5 cursor-pointer transition-colors border-b border-gray-800/50 last:border-0">
                                                    {movie.poster ? <img src={movie.poster} alt={movie.title} className="w-12 h-16 object-cover rounded-md shadow-md" /> : <div className="w-12 h-16 bg-gray-800 rounded-md flex items-center justify-center"><ImageIcon className="text-gray-500"/></div>}
                                                    <div>
                                                        <h4 className="text-white font-bold">{movie.title}</h4>
                                                        <p className="text-gray-400 text-sm">{movie.year}</p>
                                                    </div>
                                                </li>
                                            ))}
                                        </ul>
                                    ) : (
                                        <div className="p-6 text-center text-gray-400">No movies found. Try another title.</div>
                                    )}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </form>

                    {message && <div className="p-4 mb-8 bg-green-500/10 border border-green-500/20 text-green-400 rounded-xl text-center font-medium">{message}</div>}

                    <h3 className="text-xl font-bold text-white mb-6">Your Previous Requests</h3>
                    {requests.length === 0 ? (
                        <p className="text-gray-500 text-center py-10 bg-gray-900/30 rounded-2xl border border-white/5">You haven't requested any movies yet.</p>
                    ) : (
                        <div className="space-y-4">
                            {requests.map(req => (
                                <div key={req.id} className="bg-gray-900/60 p-5 rounded-xl flex justify-between items-center border border-white/5 hover:border-white/10 transition-colors shadow-lg">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center"><Film className="text-gray-400" size={20}/></div>
                                        <span className="text-white font-bold text-lg">{req.title}</span>
                                    </div>
                                    <span className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                                        req.status === 'approved' ? 'bg-green-500/10 text-green-400 border border-green-500/20' :
                                        req.status === 'fulfilled' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                                        req.status === 'rejected' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                                        'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                                    }`}>
                                        {req.status}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                  </motion.div>
                )}

                {/* ── HISTORY TAB ────────────────────────────────────────────── */}
                {activeTab === 'history' && (
                  <motion.div key="history" initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}}>
                    <h2 className="text-3xl font-display font-bold text-white mb-2">Chat History</h2>
                    <p className="text-gray-400 mb-8">Review your past cinematic deep-dives.</p>

                    {chatHistory.length === 0 ? (
                        <div className="text-center py-20 bg-gray-900/30 rounded-2xl border border-white/5">
                            <MessageSquare className="mx-auto text-gray-700 mb-4" size={64} />
                            <p className="text-gray-400 text-lg">No chat history found.</p>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {chatHistory.map((chat) => (
                                <div key={chat.id} className="bg-gray-900/50 rounded-2xl border border-white/5 p-6 md:p-8 flex flex-col gap-6 group hover:border-white/10 transition-colors shadow-lg relative overflow-hidden">
                                    <div className="flex justify-between items-start border-b border-white/5 pb-4">
                                        <div className="flex gap-4 text-sm text-gray-500 font-medium">
                                            <span className="flex items-center gap-1.5"><Calendar size={14} /> {new Date(chat.timestamp).toLocaleString()}</span>
                                            {chat.movie_name && (
                                                <span className="flex items-center gap-1.5 text-white bg-white/10 px-3 py-1 rounded-full border border-white/10">
                                                    <Film size={14} /> {chat.movie_name}
                                                </span>
                                            )}
                                        </div>
                                        <button 
                                            onClick={() => handleDeleteHistory(chat.id)}
                                            className="text-gray-500 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all p-2 rounded-lg hover:bg-red-500/10"
                                            title="Delete"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    </div>
                                    <div className="space-y-4">
                                        <div className="flex gap-4">
                                            <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center shrink-0 border border-white/10"><UserIcon size={14} className="text-gray-400"/></div>
                                            <p className="text-white font-medium text-lg leading-relaxed pt-1">{chat.question}</p>
                                        </div>
                                        <div className="flex gap-4 bg-black/20 p-4 rounded-xl border border-white/5">
                                            <div className="w-8 h-8 rounded-full bg-film-accent/20 flex items-center justify-center shrink-0 border border-film-accent/30"><Brain size={14} className="text-film-accent"/></div>
                                            <p className="text-gray-300 leading-relaxed whitespace-pre-wrap pt-1">{chat.ai_response}</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                  </motion.div>
                )}

                {/* ── PROFILE TAB ────────────────────────────────────────────── */}
                {activeTab === 'profile' && (
                  <motion.div key="profile" initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}} className="max-w-2xl">
                    <h2 className="text-3xl font-display font-bold text-white mb-2">Your Profile</h2>
                    <p className="text-gray-400 mb-8">Update your personal information.</p>

                    {message && <div className={`p-4 mb-8 rounded-xl text-center font-medium ${message.includes('successfully') ? 'bg-green-500/10 border-green-500/20 text-green-400' : 'bg-red-500/10 border-red-500/20 text-red-400'} border`}>{message}</div>}

                    <form onSubmit={handleProfileUpdate} className="space-y-6 bg-gray-900/50 p-8 rounded-2xl border border-white/5 shadow-xl">
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-2">Username</label>
                            <input 
                                type="text" 
                                value={profileForm.username}
                                onChange={(e) => setProfileForm({...profileForm, username: e.target.value})}
                                className="w-full bg-black/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-film-accent outline-none transition-colors"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-2">Email Address</label>
                            <input 
                                type="email" 
                                value={profileForm.email}
                                onChange={(e) => setProfileForm({...profileForm, email: e.target.value})}
                                className="w-full bg-black/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-film-accent outline-none transition-colors"
                            />
                        </div>
                        <div className="pt-4">
                            <button type="submit" className="w-full bg-red-gradient text-white font-bold py-4 rounded-xl shadow-button hover:shadow-[0_0_20px_rgba(229,9,20,0.4)] transition-all">
                                Save Changes
                            </button>
                        </div>
                    </form>
                  </motion.div>
                )}

                {/* ── SETTINGS TAB ───────────────────────────────────────────── */}
                {activeTab === 'settings' && (
                  <motion.div key="settings" initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}} className="max-w-2xl">
                    <h2 className="text-3xl font-display font-bold text-white mb-2">App Settings</h2>
                    <p className="text-gray-400 mb-8">Manage your application preferences.</p>

                    <div className="bg-gray-900/50 p-8 rounded-2xl border border-white/5 shadow-xl space-y-8">
                        {/* Theme Toggle Placeholder */}
                        <div className="flex items-center justify-between">
                            <div>
                                <h4 className="text-white font-bold text-lg">Dark Mode</h4>
                                <p className="text-gray-500 text-sm">Experience the premium dark cinematic theme.</p>
                            </div>
                            <div className="relative inline-block w-12 h-6 rounded-full bg-film-accent shadow-inner">
                                <div className="absolute top-1 left-7 w-4 h-4 bg-white rounded-full shadow-sm transition-all"></div>
                            </div>
                        </div>
                        
                        <div className="h-px bg-white/5"></div>

                        {/* Notifications Placeholder */}
                        <div className="flex items-center justify-between">
                            <div>
                                <h4 className="text-white font-bold text-lg">Email Notifications</h4>
                                <p className="text-gray-500 text-sm">Receive updates when your requested movies are added.</p>
                            </div>
                            <div className="relative inline-block w-12 h-6 rounded-full bg-gray-700 shadow-inner cursor-pointer hover:bg-gray-600 transition-colors">
                                <div className="absolute top-1 left-1 w-4 h-4 bg-gray-400 rounded-full shadow-sm transition-all"></div>
                            </div>
                        </div>

                        <div className="h-px bg-white/5"></div>

                        {/* Danger Zone */}
                        <div>
                            <h4 className="text-red-400 font-bold text-lg mb-2">Danger Zone</h4>
                            <p className="text-gray-500 text-sm mb-4">Permanently delete your account and all associated data.</p>
                            <button className="border border-red-500/50 text-red-400 px-6 py-2 rounded-lg hover:bg-red-500/10 transition-colors font-medium text-sm">
                                Delete Account
                            </button>
                        </div>
                    </div>
                  </motion.div>
                )}

              </AnimatePresence>
            </motion.div>
          </main>
        </div>
      </div>
    </div>
  );
}
