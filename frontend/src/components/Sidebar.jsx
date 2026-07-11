import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, MessageCircle, Film, Clock, Trash2, Loader2 } from 'lucide-react'
import { useChat } from '../context/ChatContext'
import { movieAPI } from '../services/api'
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

// Extract a movie title from a user message
function extractMovieTitle(text) {
  const lower = text.toLowerCase()
  const knownMovies = [
    'inception', 'interstellar', 'the dark knight', 'batman begins',
    'memento', 'tenet', 'oppenheimer', 'the prestige', 'dunkirk',
    '500 days of summer', 'deadpool', 'spider-man', 'beauty and the beast',
    'bones and all', 'superman', 'frankenstein', 'hamnet', 'the dark knight rises',
    'project hail mary',
  ]
  for (const title of knownMovies) {
    if (lower.includes(title)) return title
  }
  // Try to extract quoted titles
  const quoted = text.match(/[""]([^""]+)[""]/)?.[1]
  if (quoted) return quoted
  return null
}

export default function Sidebar({ onNewChat }) {
  const { messages, movieContext, setMovieContext } = useChat()
  const [activeTab,  setActiveTab]  = useState('Movie')
  const [history,    setHistory]    = useState(HISTORY_MOCK)
  const [historyTab, setHistoryTab] = useState('history') // 'history' | 'info'
  const [movieData,  setMovieData]  = useState(null)
  const [fetching,   setFetching]   = useState(false)

  const removeHistory = (id) => setHistory(h => h.filter(i => i.id !== id))

  // Auto-detect movie from messages and fetch details
  useEffect(() => {
    const userMessages = messages.filter(m => m.role === 'user')
    if (userMessages.length === 0) return

    const lastMsg = userMessages[userMessages.length - 1].content
    const title   = extractMovieTitle(lastMsg)

    if (!title || title === movieContext?.titleKey) return

    setFetching(true)
    movieAPI.getMovieDetails(title)
      .then((data) => {
        setMovieData(data)
        setMovieContext({ ...data, titleKey: title })
      })
      .catch(() => {
        // silently fail — sidebar just shows default
      })
      .finally(() => setFetching(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages])

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
