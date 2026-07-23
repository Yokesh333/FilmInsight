import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, MessageCircle, Film, Clock, Trash2, Loader2 } from 'lucide-react'
import { useChat } from '../context/ChatContext'
import { movieAPI } from '../services/api'
import { useMovies } from '../context/MovieContext'
import MovieDetailsCard from './MovieDetailsCard'
import TriviaCard from './TriviaCard'
import CastCard from './CastCard'
import QuoteCard from './QuoteCard'

const HISTORY_MOCK = [
  { id: 1, title: 'Why did Summer leave Tom?',          time: '2m ago' },
  { id: 2, title: "Explain Inception's ending",         time: '1h ago' },
  { id: 3, title: 'Character analysis of Joker',        time: 'Yesterday' },
  { id: 4, title: 'Themes in Interstellar',             time: 'Yesterday' },
]

const SIDEBAR_TABS = ['Movie', 'Cast', 'Quotes', 'Trivia']

export default function Sidebar({ onNewChat }) {
  const { messages, movieContext, setMovieContext, movieTitle } = useChat()
  const { movies: libraryMovies } = useMovies()
  const [activeTab,  setActiveTab]  = useState('Movie')
  const [history,    setHistory]    = useState(HISTORY_MOCK)
  const [historyTab, setHistoryTab] = useState('history') // 'history' | 'info'
  const [movieData,  setMovieData]  = useState(null)
  const [fetching,   setFetching]   = useState(false)

  const removeHistory = (id) => setHistory(h => h.filter(i => i.id !== id))

  // When Chat.jsx stamps a new movieTitle from the URL, fetch sidebar details
  // for that movie immediately (before any messages arrive).
  useEffect(() => {
    if (!movieTitle) {
      // Movie was cleared — reset sidebar data too
      setMovieData(null)
      return
    }
    // Avoid re-fetching if we already have data for this title
    if (movieData?.titleKey === movieTitle) return

    setFetching(true)
    movieAPI.getMovieDetails(movieTitle)
      .then((data) => {
        setMovieData({ ...data, titleKey: movieTitle })
        setMovieContext({ ...data, titleKey: movieTitle })
      })
      .catch(() => { /* silently fail */ })
      .finally(() => setFetching(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [movieTitle])

  // Auto-detect movie from messages and fetch details
  useEffect(() => {
    const userMessages = messages.filter(m => m.role === 'user')
    if (userMessages.length === 0) return

    const lastMsg = userMessages[userMessages.length - 1].content
    
    // Dynamic movie title extraction from registry
    const lower = lastMsg.toLowerCase()
    const readyMovies = libraryMovies.filter(m => m.status === 'READY')
    const sortedMovies = [...readyMovies].sort((a, b) => b.title.length - a.title.length)
    
    let title = null
    for (const movie of sortedMovies) {
      const movieTitleLower = movie.title.toLowerCase()
      if (lower.includes(movieTitleLower)) {
        title = movie.title
        break
      }
    }
    
    if (!title) {
      const quoted = lastMsg.match(/["'\u2018\u2019]([^"'\u2018\u2019]+)["'\u2018\u2019]/)?.[1]
      if (quoted) title = quoted
    }

    // Guard: skip if this title is already what's displayed, or if the URL-based
    // movieTitle already covers it (to avoid overwriting a correct context).
    if (!title) return
    if (movieData?.titleKey === title) return
    if (movieTitle && movieTitle.toLowerCase() === title.toLowerCase()) return

    setFetching(true)
    movieAPI.getMovieDetails(title)
      .then((data) => {
        setMovieData({ ...data, titleKey: title })
        setMovieContext({ ...data, titleKey: title })
      })
      .catch(() => {
        // silently fail — sidebar just shows default
      })
      .finally(() => setFetching(false))
  }, [messages, libraryMovies])

  // Sync from movieContext if set externally
  useEffect(() => {
    if (movieContext && !movieData) {
      setMovieData(movieContext)
    }
  }, [movieContext, movieData])

  // Build sidebar card data from API response
  const sidebarMovie = movieData
    ? {
        title:    movieData.title,
        year:     movieData.year,
        rating:   movieData.rating,
        runtime:  movieData.runtime,
        genre:    Array.isArray(movieData.genre) ? movieData.genre : (movieData.genre ? [movieData.genre] : []),
        director: movieData.director,
        cast:     Array.isArray(movieData.cast) ? movieData.cast : (movieData.cast ? [movieData.cast] : []),
        plot:     movieData.plot || movieData.overview,
        awards:   movieData.awards,
        poster:   movieData.poster,
        backdrop: movieData.backdrop,
        tagline:  movieData.tagline,
        imdb_id:  movieData.imdb_id,
        status:   'loaded',
      }
    : undefined

  const triviaItems = (movieData?.trivia || []).map(fact => ({ fact, tag: 'Behind the Scenes' }))
  const quoteItems  = movieData?.quotes || []
  const castItems   = sidebarMovie?.cast.map(name => ({ name, role: '' })) || []

  return (
    <div className="flex flex-col h-full gap-3 px-3 py-4">
      {/* New Chat */}
      <button
        onClick={onNewChat}
        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 glass border border-white/10 rounded-xl text-sm font-medium text-film-subtle hover:text-white hover:border-film-red/30 hover:bg-film-red/5 transition-all"
      >
        <Plus size={15} />
        New Chat
      </button>

      {/* Tabs */}
      <div className="flex gap-1 glass border border-white/8 rounded-xl p-1">
        {['history', 'info'].map((t) => (
          <button
            key={t}
            onClick={() => setHistoryTab(t)}
            className={`flex-1 py-1.5 text-xs rounded-lg font-medium transition-all ${
              historyTab === t ? 'bg-film-red text-white' : 'text-film-muted hover:text-white'
            }`}
          >
            {t === 'history' ? '💬 History' : '🎬 Movie'}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {historyTab === 'history' ? (
          <motion.div
            key="history"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="flex-1 overflow-y-auto space-y-1 min-h-0"
          >
            {history.length === 0 ? (
              <div className="text-center py-8 text-film-muted text-xs">No chat history yet.</div>
            ) : (
              history.map((item) => (
                <div
                  key={item.id}
                  className="group flex items-start gap-2 px-3 py-2.5 rounded-xl hover:bg-white/4 transition-colors cursor-pointer"
                >
                  <MessageCircle size={13} className="text-film-muted flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-film-subtle truncate group-hover:text-white transition-colors">
                      {item.title}
                    </p>
                    <div className="flex items-center gap-1 mt-0.5">
                      <Clock size={9} className="text-film-muted" />
                      <span className="text-[10px] text-film-muted">{item.time}</span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); removeHistory(item.id) }}
                    className="opacity-0 group-hover:opacity-100 p-0.5 text-film-muted hover:text-film-red transition-all"
                  >
                    <Trash2 size={11} />
                  </button>
                </div>
              ))
            )}
          </motion.div>
        ) : (
          <motion.div
            key="info"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="flex-1 overflow-y-auto min-h-0 space-y-3"
          >
            {/* Fetching indicator */}
            {fetching && (
              <div className="flex items-center gap-2 text-xs text-film-muted px-2">
                <Loader2 size={12} className="animate-spin" />
                Fetching movie data…
              </div>
            )}

            {/* Sub-tabs */}
            <div className="grid grid-cols-4 gap-1">
              {SIDEBAR_TABS.map((t) => (
                <button
                  key={t}
                  onClick={() => setActiveTab(t)}
                  className={`py-1 text-[10px] rounded-lg font-medium transition-all ${
                    activeTab === t ? 'bg-white/10 text-white' : 'text-film-muted hover:text-white'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                {activeTab === 'Movie'  && <MovieDetailsCard movie={sidebarMovie} />}
                {activeTab === 'Cast'   && <CastCard cast={castItems.length > 0 ? castItems : undefined} />}
                {activeTab === 'Quotes' && <QuoteCard quotes={quoteItems.length > 0 ? quoteItems : undefined} />}
                {activeTab === 'Trivia' && <TriviaCard trivia={triviaItems.length > 0 ? triviaItems : undefined} />}
              </motion.div>
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
