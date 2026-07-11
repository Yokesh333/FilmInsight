import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search, Sparkles, TrendingUp, Clock, ChevronRight,
  Film, Brain, MessageCircle, Quote, Lightbulb, Star,
  Zap, Users, BookOpen, X,
} from 'lucide-react'

/* ── Data ──────────────────────────────────────────────────────── */
const SUGGESTED_QUESTIONS = [
  { text: 'Explain the ending of Interstellar.', tag: 'Plot' },
  { text: 'Why did Summer leave Tom?', tag: 'Character' },
  { text: "Analyze Joker's character arc.", tag: 'Analysis' },
  { text: 'What is the hidden meaning behind Inception?', tag: 'Theme' },
  { text: 'Explain the relationship between Tom and Summer.', tag: 'Character' },
  { text: 'What does the color red symbolize in American Beauty?', tag: 'Symbolism' },
  { text: 'Describe the narrative structure of Pulp Fiction.', tag: 'Structure' },
  { text: 'Why is the ending of La La Land bittersweet?', tag: 'Theme' },
]

const POPULAR_MOVIES = [
  { id: 1, title: '500 Days of Summer', genre: 'Romance · Drama',     year: 2009, rating: '7.7', gradient: 'from-sky-900   via-indigo-900 to-blue-950',   emoji: '💙' },
  { id: 2, title: 'Inception',          genre: 'Sci-Fi · Thriller',   year: 2010, rating: '8.8', gradient: 'from-slate-900 via-gray-800   to-zinc-900',    emoji: '🌀' },
  { id: 3, title: 'Interstellar',       genre: 'Sci-Fi · Drama',      year: 2014, rating: '8.7', gradient: 'from-amber-950 via-orange-900 to-yellow-950',  emoji: '🪐' },
  { id: 4, title: 'The Dark Knight',    genre: 'Action · Crime',      year: 2008, rating: '9.0', gradient: 'from-gray-950  via-zinc-900   to-neutral-900', emoji: '🦇' },
  { id: 5, title: 'Parasite',           genre: 'Drama · Thriller',    year: 2019, rating: '8.5', gradient: 'from-green-950 via-teal-900   to-emerald-950', emoji: '🏚️' },
  { id: 6, title: 'La La Land',         genre: 'Romance · Musical',   year: 2016, rating: '8.0', gradient: 'from-purple-900 via-violet-800 to-indigo-900', emoji: '🎷' },
  { id: 7, title: 'Whiplash',           genre: 'Drama · Music',       year: 2014, rating: '8.5', gradient: 'from-red-950   via-rose-900   to-red-900',     emoji: '🥁' },
  { id: 8, title: 'Fight Club',         genre: 'Drama · Thriller',    year: 1999, rating: '8.8', gradient: 'from-yellow-900 via-amber-800  to-orange-900', emoji: '🥊' },
]

const FEATURES = [
  { icon: Brain,       title: 'AI Plot Analysis',      desc: 'Deep analysis of plot structure and narrative arcs.',     color: 'text-red-400',    bg: 'bg-red-500/10' },
  { icon: Users,       title: 'Character Insights',    desc: 'Explore character development and motivations.',          color: 'text-blue-400',   bg: 'bg-blue-500/10' },
  { icon: BookOpen,    title: 'Scene Explanation',     desc: 'Understand pivotal scenes and their significance.',       color: 'text-green-400',  bg: 'bg-green-500/10' },
  { icon: Lightbulb,   title: 'Movie Trivia',          desc: 'Behind-the-scenes facts and interesting trivia.',         color: 'text-amber-400',  bg: 'bg-amber-500/10' },
  { icon: Quote,       title: 'Famous Quotes',         desc: 'Discover memorable lines and their context.',             color: 'text-pink-400',   bg: 'bg-pink-500/10' },
  { icon: Star,        title: 'IMDb Information',      desc: 'Ratings, cast info, and production details.',             color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
]

/* ── Sub-components ────────────────────────────────────────────── */
function SearchBar({ onSubmit }) {
  const [query,   setQuery]   = useState('')
  const [focused, setFocused] = useState(false)
  const inputRef = useRef(null)

  const handleSubmit = (e) => {
    e?.preventDefault()
    if (query.trim()) onSubmit(query.trim())
  }

  return (
    <form onSubmit={handleSubmit} className="relative w-full max-w-2xl mx-auto">
      <div className={`relative flex items-center rounded-2xl border transition-all duration-300 ${
        focused
          ? 'border-film-red/60 shadow-[0_0_0_4px_rgba(229,9,20,0.1)]'
          : 'border-white/10 hover:border-white/20'
      } bg-film-card`}>
        <div className="pl-5 pr-3 flex-shrink-0">
          <Search size={20} className={`transition-colors ${focused ? 'text-film-red' : 'text-film-muted'}`} />
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
          <button
            type="button"
            onClick={() => setQuery('')}
            className="px-2 text-film-muted hover:text-white"
          >
            <X size={16} />
          </button>
        )}
        <button
          type="submit"
          disabled={!query.trim()}
          className="m-2 px-5 py-2.5 bg-red-gradient rounded-xl text-sm font-semibold text-white disabled:opacity-40 hover:opacity-90 transition-opacity flex-shrink-0"
        >
          Ask AI
        </button>
      </div>
    </form>
  )
}

function MovieCard({ movie, onClick }) {
  return (
    <motion.div
      whileHover={{ y: -8, scale: 1.03 }}
      whileTap={{ scale: 0.97 }}
      onClick={() => onClick(movie)}
      className="cursor-pointer group"
    >
      {/* Poster */}
      <div className={`relative h-48 rounded-2xl bg-gradient-to-br ${movie.gradient} mb-3 overflow-hidden border border-white/5 group-hover:border-white/15 transition-all`}>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-5xl opacity-30 group-hover:opacity-50 group-hover:scale-110 transition-all duration-300">
            {movie.emoji}
          </span>
        </div>
        {/* Overlay on hover */}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            whileHover={{ opacity: 1, scale: 1 }}
            className="opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <div className="px-3 py-1.5 bg-film-red rounded-lg text-xs font-semibold text-white flex items-center gap-1.5">
              <MessageCircle size={12} />
              Ask About This
            </div>
          </motion.div>
        </div>
        {/* Rating badge */}
        <div className="absolute top-2 right-2 flex items-center gap-1 px-2 py-0.5 bg-black/60 backdrop-blur-sm rounded-full">
          <Star size={10} className="text-film-gold" fill="currentColor" />
          <span className="text-xs font-bold text-white">{movie.rating}</span>
        </div>
      </div>
      {/* Info */}
      <h3 className="font-display font-bold text-white text-sm leading-tight mb-0.5 group-hover:text-film-red transition-colors">
        {movie.title}
      </h3>
      <p className="text-xs text-film-muted">{movie.genre} · {movie.year}</p>
    </motion.div>
  )
}

/* ── Page ──────────────────────────────────────────────────────── */
export default function Home() {
  const navigate = useNavigate()
  const [recentSearches, setRecentSearches] = useState([])

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem('fi_recent') || '[]')
    setRecentSearches(stored.slice(0, 5))
  }, [])

  const handleSearch = (query) => {
    // Save to recent
    const updated = [query, ...recentSearches.filter(q => q !== query)].slice(0, 5)
    localStorage.setItem('fi_recent', JSON.stringify(updated))
    navigate(`/chat?q=${encodeURIComponent(query)}`)
  }

  const handleMovieClick = (movie) => {
    const q = `Tell me about "${movie.title}" — plot, characters, and themes.`
    handleSearch(q)
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
      transition={{ duration: 0.4 }}
      className="min-h-screen"
    >
      {/* ── Hero / Search ─────────────────────────────────────── */}
      <section className="relative pt-28 pb-16 px-4 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-20 left-1/4 w-96 h-96 bg-film-red/6 rounded-full blur-3xl" />
          <div className="absolute top-40 right-1/4 w-72 h-72 bg-blue-900/8 rounded-full blur-3xl" />
          <div className="absolute inset-0 opacity-[0.02]"
            style={{ backgroundImage:'radial-gradient(rgba(255,255,255,0.8) 1px, transparent 1px)', backgroundSize:'32px 32px' }}
          />
        </div>

        <div className="relative max-w-4xl mx-auto text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 glass border border-film-red/20 rounded-full px-4 py-1.5 mb-6 text-xs font-medium text-film-subtle"
          >
            <Sparkles size={12} className="text-film-red" />
            Powered by RAG · Groq · Flowise
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="font-display font-black text-5xl sm:text-6xl lg:text-7xl text-white mb-3 leading-none"
          >
            <span className="gradient-text">FilmInsight</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.12 }}
            className="text-film-subtle text-xl mb-10"
          >
            Your AI-powered Movie Companion
          </motion.p>

          {/* Search Bar */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.18 }}
          >
            <SearchBar onSubmit={handleSearch} />
          </motion.div>

          {/* Suggested Questions */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.28 }}
            className="mt-6"
          >
            <p className="text-xs text-film-muted mb-3 flex items-center justify-center gap-1.5">
              <TrendingUp size={11} /> Try asking
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTED_QUESTIONS.slice(0, 5).map((s) => (
                <button
                  key={s.text}
                  onClick={() => handleSearch(s.text)}
                  className="text-xs px-3 py-1.5 glass border border-white/8 rounded-full text-film-subtle hover:text-white hover:border-film-red/30 hover:bg-film-red/5 transition-all duration-200"
                >
                  {s.text}
                </button>
              ))}
            </div>
          </motion.div>

          {/* Recent Searches */}
          <AnimatePresence>
            {recentSearches.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-6"
              >
                <p className="text-xs text-film-muted mb-2 flex items-center justify-center gap-1.5">
                  <Clock size={11} /> Recent searches
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {recentSearches.map((item) => (
                    <div
                      key={item}
                      className="flex items-center gap-1.5 text-xs px-3 py-1.5 glass border border-white/5 rounded-full text-film-muted group"
                    >
                      <button onClick={() => handleSearch(item)} className="hover:text-white transition-colors truncate max-w-[180px]">
                        {item}
                      </button>
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

      {/* ── Popular Movies ─────────────────────────────────────── */}
      <section className="px-4 pb-16">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Film size={18} className="text-film-red" />
              <h2 className="font-display font-bold text-xl text-white">Popular Movies</h2>
            </div>
            <span className="text-xs text-film-muted">Click to start chatting</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 xl:gap-5">
            {POPULAR_MOVIES.map((movie, i) => (
              <motion.div
                key={movie.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.07 }}
              >
                <MovieCard movie={movie} onClick={handleMovieClick} />
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Feature Cards ──────────────────────────────────────── */}
      <section className="px-4 pb-20">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center gap-2 mb-6">
            <Zap size={18} className="text-film-red" />
            <h2 className="font-display font-bold text-xl text-white">What FilmInsight Can Do</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map(({ icon: Icon, title, desc, color, bg }, i) => (
              <motion.div
                key={title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                whileHover={{ y: -4 }}
                className="glass border border-white/8 rounded-2xl p-5 hover:border-white/15 transition-all group cursor-pointer"
                onClick={() => handleSearch(`Show me an example of ${title.toLowerCase()} for a movie.`)}
              >
                <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
                  <Icon size={20} className={color} />
                </div>
                <h3 className="font-display font-semibold text-white text-sm mb-1">{title}</h3>
                <p className="text-film-muted text-xs leading-relaxed">{desc}</p>
                <div className="flex items-center gap-1 mt-3 text-xs text-film-muted group-hover:text-film-red transition-colors">
                  Try it <ChevronRight size={11} />
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </motion.div>
  )
}
