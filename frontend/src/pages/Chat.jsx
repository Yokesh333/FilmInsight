import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Menu, X, Info } from 'lucide-react'
import { useChat } from '../context/ChatContext'
import { chatAPI } from '../services/api'
import ChatWindow from '../components/ChatWindow'
import Sidebar from '../components/Sidebar'

export default function Chat() {
  const [searchParams] = useSearchParams()
  const { addMessage, setLoading, setError, sessionId, clearChat } = useChat()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [infoOpen,    setInfoOpen]    = useState(false)

  // Handle ?q= from navigation
  useEffect(() => {
    const query = searchParams.get('q')
    if (!query) return

    const ask = async () => {
      addMessage({ role: 'user', content: query })
      setLoading(true)
      try {
        const data = await chatAPI.sendMessage(query, sessionId)
        addMessage({
          role: 'assistant',
          content: data.answer || 'No response received.',
          sources: data.sources || [],
        })
      } catch (err) {
        addMessage({ role: 'assistant', content: `⚠️ **Error**: ${err.message}`, sources: [] })
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    ask()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleNewChat = () => {
    clearChat()
    setSidebarOpen(false)
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      className="pt-16 h-screen flex overflow-hidden"
    >
      {/* ── Left Sidebar ──────────────────────────────────────── */}
      {/* Desktop */}
      <div className="hidden lg:flex w-64 xl:w-72 flex-shrink-0 border-r border-white/5 h-full bg-film-surface/40 overflow-hidden">
        <div className="w-full overflow-y-auto">
          <Sidebar onNewChat={handleNewChat} />
        </div>
      </div>

      {/* Mobile Sidebar Drawer */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-40">
          <div className="absolute inset-0 bg-black/60" onClick={() => setSidebarOpen(false)} />
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', damping: 28 }}
            className="absolute left-0 top-0 bottom-0 w-72 bg-film-surface border-r border-white/8 z-50"
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
              <span className="font-semibold text-sm text-white">Menu</span>
              <button onClick={() => setSidebarOpen(false)} className="text-film-muted hover:text-white">
                <X size={18} />
              </button>
            </div>
            <Sidebar onNewChat={handleNewChat} />
          </motion.div>
        </div>
      )}

      {/* ── Main Chat ─────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col h-full min-w-0 relative">
        {/* Mobile top controls */}
        <div className="flex lg:hidden items-center gap-2 px-4 py-2 border-b border-white/5 bg-film-surface/30">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-lg hover:bg-white/5 text-film-muted hover:text-white transition-colors"
          >
            <Menu size={18} />
          </button>
          <span className="text-sm font-medium text-film-subtle flex-1 text-center">FilmInsight AI</span>
          <button
            onClick={() => setInfoOpen(!infoOpen)}
            className="p-2 rounded-lg hover:bg-white/5 text-film-muted hover:text-white transition-colors"
          >
            <Info size={18} />
          </button>
        </div>

        <ChatWindow onNewChat={handleNewChat} />
      </div>

      {/* ── Right Info Panel (Desktop) ────────────────────────── */}
      <div className="hidden xl:flex w-60 flex-shrink-0 border-l border-white/5 h-full flex-col p-4 bg-film-surface/20 gap-4 overflow-y-auto">
        {/* Model Info */}
        <div className="glass border border-white/8 rounded-2xl p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-film-muted mb-3">Model</p>
          <div className="space-y-2 text-xs">
            {[
              ['LLM',        'Groq · LLaMA 3'],
              ['Retrieval',  'HuggingFace + Chroma'],
              ['Framework',  'Flowise RAG'],
              ['Backend',    'FastAPI'],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between items-center">
                <span className="text-film-muted">{k}</span>
                <span className="text-film-subtle font-medium text-right">{v}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Tips */}
        <div className="glass border border-white/8 rounded-2xl p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-film-muted mb-3">Tips</p>
          <ul className="space-y-2 text-xs text-film-muted">
            {[
              'Mention the movie title for precise answers',
              'Ask for specific scenes or dialogues',
              'Request character comparisons',
              'Explore hidden symbolism',
              'Ask for famous quotes by character',
            ].map((tip) => (
              <li key={tip} className="flex items-start gap-1.5 leading-snug">
                <span className="text-film-red mt-0.5 flex-shrink-0">•</span>
                {tip}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </motion.div>
  )
}
