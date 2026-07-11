import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Mic, ArrowRight, Clock, TrendingUp } from 'lucide-react'

const SUGGESTIONS = [
  { text: 'Why did Summer leave Tom in 500 Days of Summer?', category: 'Plot' },
  { text: "Explain the non-linear narrative of Inception", category: 'Structure' },
  { text: 'What is the main theme of Interstellar?',        category: 'Theme' },
  { text: "Describe Heath Ledger's Joker character",       category: 'Character' },
  { text: 'Famous quotes from The Dark Knight',             category: 'Quotes' },
]

export default function MovieSearchBar({ onSearch }) {
  const navigate = useNavigate()
  const [query,   setQuery]   = useState('')
  const [focused, setFocused] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!query.trim()) return
    if (onSearch) {
      onSearch(query.trim())
    } else {
      navigate(`/chat?q=${encodeURIComponent(query.trim())}`)
    }
    setQuery('')
    setFocused(false)
  }

  const handleSuggestion = (text) => {
    if (onSearch) {
      onSearch(text)
    } else {
      navigate(`/chat?q=${encodeURIComponent(text)}`)
    }
    setFocused(false)
  }

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit}>
        <div className={`relative flex items-center transition-all duration-300 rounded-2xl border ${
          focused
            ? 'border-film-red/50 shadow-glow-red'
            : 'border-white/8 hover:border-white/15'
        } glass`}>
          <Search
            size={18}
            className={`ml-4 flex-shrink-0 transition-colors ${focused ? 'text-film-red' : 'text-film-muted'}`}
          />
          <input
            type="text"
            id="movie-search-bar"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setTimeout(() => setFocused(false), 200)}
            placeholder="Ask about any movie, character, scene, or quote..."
            className="flex-1 px-4 py-4 bg-transparent text-white placeholder-film-muted text-sm outline-none"
          />
          {query && (
            <motion.button
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              type="submit"
              className="mr-2 flex items-center gap-1.5 px-4 py-2 bg-red-gradient rounded-xl text-xs font-semibold text-white hover:opacity-90 transition-opacity"
            >
              Ask <ArrowRight size={13} />
            </motion.button>
          )}
        </div>
      </form>

      {/* Dropdown suggestions */}
      <AnimatePresence>
        {focused && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            transition={{ duration: 0.2 }}
            className="absolute top-full mt-2 left-0 right-0 glass-strong border border-white/8 rounded-2xl overflow-hidden shadow-glass z-30"
          >
            <div className="p-3">
              <div className="flex items-center gap-2 px-2 mb-2">
                <TrendingUp size={12} className="text-film-red" />
                <span className="text-xs text-film-muted uppercase tracking-wider">Suggested Questions</span>
              </div>
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  onMouseDown={() => handleSuggestion(s.text)}
                  className="w-full flex items-center justify-between gap-3 px-3 py-2.5 rounded-xl hover:bg-white/5 transition-colors text-left group"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Clock size={13} className="text-film-muted flex-shrink-0" />
                    <span className="text-sm text-film-subtle group-hover:text-white truncate transition-colors">
                      {s.text}
                    </span>
                  </div>
                  <span className="flex-shrink-0 text-xs px-2 py-0.5 rounded-full glass border border-white/8 text-film-muted">
                    {s.category}
                  </span>
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
