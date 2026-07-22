import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search, Sparkles, TrendingUp, Clock, ChevronRight,
  Film, Brain, MessageCircle, Quote, Lightbulb, Star,
  Zap, Users, BookOpen, X, ArrowRight, Play, AlertCircle,
} from 'lucide-react'
import { movieAPI, favoritesAPI, recentAPI } from '../services/api'
import MovieCard from '../components/MovieCard'
import { useAuth } from '../context/AuthContext'

/* ── Data ─────────────────────────────────────────────────────── */
const SUGGESTED = [
  { text: 'Explain the ending of Interstellar.',           tag: 'Plot' },
  { text: 'Why did Summer leave Tom?',                     tag: 'Character' },
  { text: "Analyze Joker's character arc.",                tag: 'Analysis' },
  { text: 'Hidden meaning behind Inception?',             tag: 'Theme' },
  { text: 'Describe the narrative structure of Tenet.',   tag: 'Structure' },
  { text: "What makes Oppenheimer's ending powerful?",    tag: 'Theme' },
]

const FEATURES = [
  { icon: Brain,       title: 'AI Plot Analysis',   desc: 'Deep analysis of plot structure and narrative arcs.',  color:'text-red-400',    bg:'bg-red-500/10',    border:'hover:border-red-500/20' },
  { icon: Users,       title: 'Character Insights', desc: 'Explore character development and motivations.',        color:'text-blue-400',   bg:'bg-blue-500/10',   border:'hover:border-blue-500/20' },
  { icon: BookOpen,    title: 'Scene Explanation',  desc: 'Understand pivotal scenes and their significance.',     color:'text-green-400',  bg:'bg-green-500/10',  border:'hover:border-green-500/20' },
  { icon: Lightbulb,   title: 'Movie Trivia',       desc: 'Behind-the-scenes facts and interesting trivia.',       color:'text-amber-400',  bg:'bg-amber-500/10',  border:'hover:border-amber-500/20' },
  { icon: Quote,       title: 'Famous Quotes',      desc: 'Discover memorable lines and their context.',           color:'text-pink-400',   bg:'bg-pink-500/10',   border:'hover:border-pink-500/20' },
  { icon: Star,        title: 'IMDb Information',   desc: 'Ratings, cast info, and production details.',           color:'text-yellow-400', bg:'bg-yellow-500/10', border:'hover:border-yellow-500/20' },
]

/* ── Skeleton Component ──────────────────────────────────────── */
function MovieSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="skeleton rounded-2xl mb-3" style={{ aspectRatio: '2/3' }} />
      <div className="skeleton h-4 w-3/4 mb-2 rounded" />
      <div className="skeleton h-3 w-1/2 rounded" />
    </div>
  )
}

/* ── Removed inline MovieCard ────────────────────────────────── */


/* ── Search Bar ─────────────────────────────────────────────── */
function SearchBar({ onSubmit }) {
  const [query,   setQuery]   = useState('')
  const [focused, setFocused] = useState(false)
  const inputRef = useRef(null)

  const handleSubmit = (e) => { e?.preventDefault(); if (query.trim()) onSubmit(query.trim()) }

  return (
    <form onSubmit={handleSubmit} className={`relative w-full max-w-2xl mx-auto rounded-2xl transition-all duration-300 input-glow ${focused ? 'ring-2 ring-film-red/20' : ''}`}>
      <div className={`flex items-center glass-card rounded-2xl border transition-all duration-300 ${
        focused ? 'border-film-red/40 bg-white/5' : 'border-white/8 hover:border-white/14'
      }`}>
        <div className="pl-5 pr-3 flex-shrink-0">
          <motion.div animate={{ scale: focused ? 1.15 : 1, color: focused ? '#E50914' : '#5A6170' }} transition={{ duration: 0.2 }}>
            <Search size={20} />
          </motion.div>
        </div>
        <input
          ref={inputRef}
          id="home-search"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder="Ask anything about a movie..."
          className="flex-1 py-4 bg-transparent text-white placeholder-film-muted text-base outline-none"
        />
        {query && (
          <button type="button" onClick={() => setQuery('')} className="px-2 text-film-muted hover:text-white transition-colors">
            <X size={15} />
          </button>
        )}
        <motion.button
          whileTap={{ scale: 0.95 }}
          type="submit"
          disabled={!query.trim()}
          className="btn-primary m-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none"
        >
          <ArrowRight size={16} />
          Ask AI
        </motion.button>
      </div>
    </form>
  )
}

/* ── Feature Card ──────────────────────────────────────────── */
function FeatureCard({ icon: Icon, title, desc, color, bg, border, index, onClick }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.08 }}
      whileHover={{ y: -6 }}
      onClick={onClick}
      className={`card cursor-pointer p-5 border border-white/7 ${border} group`}
    >
      <div className={`w-11 h-11 rounded-xl ${bg} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
        <Icon size={22} className={color} />
      </div>
      <h3 className="font-display font-semibold text-white text-sm mb-1.5 group-hover:text-white">{title}</h3>
      <p className="text-film-muted text-xs leading-relaxed mb-3">{desc}</p>
      <div className={`flex items-center gap-1 text-xs ${color} opacity-0 group-hover:opacity-100 transition-all duration-200`}>
        Try it <ChevronRight size={11} />
      </div>
    </motion.div>
  )
}

/* ── Page ─────────────────────────────────────────────────── */
export default function Home() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [recentSearches, setRecentSearches] = useState([])
  const [loading,        setLoading]        = useState(true)
  const [movies,         setMovies]         = useState([])
  const [favorites,      setFavorites]      = useState(new Set())
  const [movieError,     setMovieError]     = useState(false)

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem('fi_recent') || '[]')
    setRecentSearches(stored.slice(0, 5))

    const fetchInitialData = async () => {
        try {
            const moviesData = await movieAPI.getOurMovies();
            setMovies(moviesData.movies || []);
            
            if (user) {
                try {
                    const favData = await favoritesAPI.getFavorites();
                    const favSet = new Set(favData.map(f => f.movie_title));
                    setFavorites(favSet);
                } catch (favErr) {
                    console.error("Failed to fetch favorites:", favErr);
                }
            }
        } catch (err) {
            setMovieError(true);
        } finally {
            setLoading(false);
        }
    };
    
    fetchInitialData();
  }, [user])

  const handleToggleFavorite = async (movie) => {
    if (!user) {
        navigate('/login');
        return;
    }
    
    const isFav = favorites.has(movie.title);
    try {
        if (isFav) {
            await favoritesAPI.removeFavorite(movie.title);
            const newFavs = new Set(favorites);
            newFavs.delete(movie.title);
            setFavorites(newFavs);
        } else {
            await favoritesAPI.addFavorite({
                movie_title: movie.title,
                movie_year: movie.year ? movie.year.toString() : null,
                poster_url: movie.poster
            });
            setFavorites(new Set(favorites).add(movie.title));
        }
    } catch (err) {
        console.error("Failed to toggle favorite", err);
    }
  }

  const handleSearch = (q) => {
    const updated = [q, ...recentSearches.filter(x => x !== q)].slice(0, 5)
    localStorage.setItem('fi_recent', JSON.stringify(updated))
    navigate(`/chat?q=${encodeURIComponent(q)}`)
  }

  const handleMovieClick = (movie) => {
    if (user) {
        recentAPI.addRecent({
            movie_title: movie.title,
            movie_year: movie.year ? movie.year.toString() : null,
            poster_url: movie.poster
        }).catch(err => console.error("Failed to add recent", err));
    }
    handleSearch(`Tell me about "${movie.title}" — plot, characters, and themes.`);
  }

  const removeRecent = (e, item) => {
    e.stopPropagation()
    const updated = recentSearches.filter(q => q !== item)
    setRecentSearches(updated)
    localStorage.setItem('fi_recent', JSON.stringify(updated))
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.45 }}
      className="min-h-screen bg-mesh"
    >
      {/* ── Hero ──────────────────────────────────────────────── */}
      <section className="relative pt-28 pb-14 px-4 overflow-hidden hero-scanline">
        {/* Background orbs */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-film-red/5 rounded-full blur-[100px]" />
          <div className="absolute top-40 left-1/4 w-64 h-64 bg-indigo-900/6 rounded-full blur-[80px]" />
          <div className="absolute top-60 right-1/4 w-48 h-48 bg-amber-900/5 rounded-full blur-[60px]" />
          {/* Grid */}
          <div className="absolute inset-0 opacity-[0.018]"
               style={{ backgroundImage:'radial-gradient(rgba(255,255,255,0.8) 1px, transparent 1px)', backgroundSize:'40px 40px' }} />
        </div>

        <div className="relative max-w-4xl mx-auto text-center">
          {/* Status badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2.5 mb-7"
          >
            <div className="flex items-center gap-2 glass border border-film-red/15 rounded-full px-4 py-1.5 text-xs font-medium text-film-subtle">
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                <span>AI Online</span>
              </div>
              <span className="text-film-muted">·</span>
              <Sparkles size={11} className="text-film-red" />
              <span>Powered by Groq · RAG · Flowise</span>
            </div>
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.07, duration: 0.6 }}
            className="font-display font-black leading-none mb-3"
            style={{ fontSize: 'clamp(3rem, 8vw, 5.5rem)' }}
          >
            <span className="gradient-text">FilmInsight</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.13 }}
            className="text-film-subtle text-lg sm:text-xl mb-10"
          >
            Your AI-powered Movie Companion
          </motion.p>

          {/* Search */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <SearchBar onSubmit={handleSearch} />
          </motion.div>

          {/* Suggested chips */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.32 }} className="mt-6">
            <p className="text-[11px] text-film-muted mb-3 flex items-center justify-center gap-1.5">
              <TrendingUp size={11} /> Try asking
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTED.map((s) => (
                <motion.button
                  key={s.text}
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => handleSearch(s.text)}
                  className="text-xs px-3 py-1.5 glass border border-white/7 rounded-full text-film-subtle hover:text-white hover:border-film-red/25 hover:bg-film-red/6 transition-all duration-200"
                >
                  {s.text}
                </motion.button>
              ))}
            </div>
          </motion.div>

          {/* Recent searches */}
          <AnimatePresence>
            {recentSearches.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-5"
              >
                <p className="text-[11px] text-film-muted mb-2 flex items-center justify-center gap-1.5">
                  <Clock size={11} /> Recent
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {recentSearches.map((item) => (
                    <div key={item} className="flex items-center gap-1.5 text-xs px-3 py-1.5 glass border border-white/5 rounded-full text-film-muted group">
                      <button onClick={() => handleSearch(item)} className="hover:text-white transition-colors truncate max-w-[200px]">{item}</button>
                      <button onClick={(e) => removeRecent(e, item)} className="opacity-0 group-hover:opacity-100 hover:text-film-red transition-all">
                        <X size={10} />
                      </button>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>

      {/* ── Stats Bar ─────────────────────────────────────────── */}
      <motion.section
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        className="px-4 pb-12"
      >
        <div className="max-w-4xl mx-auto">
          <div className="divider mb-8" />
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { value: '500+', label: 'Screenplays Indexed' },
              { value: '<1s',  label: 'Response Time' },
              { value: '98%',  label: 'Accuracy' },
              { value: 'RAG',  label: 'AI Architecture' },
            ].map(({ value, label }, i) => (
              <motion.div
                key={label}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.06 }}
                className="text-center glass border border-white/6 rounded-2xl py-4"
              >
                <p className="font-display font-black text-2xl gradient-text mb-0.5">{value}</p>
                <p className="text-xs text-film-muted">{label}</p>
              </motion.div>
            ))}
          </div>
          <div className="divider mt-8" />
        </div>
      </motion.section>

      {/* ── Our Script Movies ─────────────────────────────────── */}
      <section className="px-4 pb-16">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-7">
            <div className="flex items-center gap-2.5">
              <div className="w-1 h-5 bg-red-gradient rounded-full" />
              <Film size={17} className="text-film-red" />
              <h2 className="font-display font-bold text-xl text-white">Our Script Library</h2>
              <span className="text-xs px-2 py-0.5 rounded-full bg-film-red/15 text-film-red border border-film-red/20 font-medium">
                {movies.length > 0 ? `${movies.length} films` : 'Live'}
              </span>
            </div>
            <span className="text-xs text-film-muted glass border border-white/6 rounded-full px-3 py-1">
              Click to explore
            </span>
          </div>

          {movieError && (
            <div className="flex items-center gap-3 p-4 rounded-2xl glass border border-yellow-500/20 mb-6">
              <AlertCircle size={16} className="text-yellow-400 flex-shrink-0" />
              <p className="text-xs text-yellow-300">Could not load movies from backend. Make sure the backend server is running.</p>
            </div>
          )}

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 xl:gap-5">
            {loading
              ? Array.from({ length: 10 }).map((_, i) => <MovieSkeleton key={i} />)
              : movies.length > 0
                ? movies.map((movie, i) => (
                    <MovieCard
                      key={movie.id || i}
                      movie={movie}
                      index={i}
                      isFavorite={favorites.has(movie.title)}
                      onToggleFavorite={handleToggleFavorite}
                      onClick={() => handleMovieClick(movie)}
                    />
                  ))
                : !movieError && Array.from({ length: 10 }).map((_, i) => <MovieSkeleton key={i} />)
            }
          </div>
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────── */}
      <section className="px-4 pb-20">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 badge badge-red mb-4">
              <Zap size={11} />
              Capabilities
            </div>
            <h2 className="font-display font-bold text-3xl text-white mb-2">
              What FilmInsight <span className="gradient-text">Can Do</span>
            </h2>
            <p className="text-film-muted text-sm max-w-lg mx-auto">
              A complete AI toolkit for exploring movie screenplays with unprecedented depth.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map((f, i) => (
              <FeatureCard
                key={f.title}
                {...f}
                index={i}
                onClick={() => handleSearch(`Show me an example of ${f.title.toLowerCase()} for a movie.`)}
              />
            ))}
          </div>

          {/* CTA row */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mt-10"
          >
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => handleSearch('What can you help me with?')}
              className="btn-primary text-base px-8 py-3.5"
            >
              <MessageCircle size={18} />
              Start Chatting Now
              <ArrowRight size={16} />
            </motion.button>
          </motion.div>
        </div>
      </section>
    </motion.div>
  )
}
