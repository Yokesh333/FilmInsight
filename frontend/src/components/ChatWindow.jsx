import { useRef, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, RotateCcw, Sparkles, Plus, Film } from 'lucide-react'
import { useChat } from '../context/ChatContext'
import { chatAPI } from '../services/api'
import MessageBubble from './MessageBubble'
import LoadingAnimation from './LoadingAnimation'

const STARTER_QUESTIONS = [
  { q: 'Explain the ending of this movie.', icon: '🎬' },
  { q: 'Analyze the main character\'s arc.', icon: '👤' },
  { q: 'What are the central themes?',       icon: '💡' },
  { q: 'Give me famous quotes.',             icon: '💬' },
  { q: 'Describe the narrative structure.',  icon: '📖' },
  { q: 'What symbolism is used?',            icon: '🔍' },
]

export default function ChatWindow({ onNewChat }) {
  const { messages, isLoading, sessionId, addMessage, setLoading, setError, clearChat, movieContext, movieTitle } = useChat()
  const [input, setInput]   = useState('')
  const endRef              = useRef(null)
  const inputRef            = useRef(null)
  const messagesRef         = useRef(null)

  // Auto-scroll
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Focus input on mount
  useEffect(() => { inputRef.current?.focus() }, [])

  const handleSend = async (text) => {
    const question = (text || input).trim()
    if (!question || isLoading) return

    setInput('')
    addMessage({ role: 'user', content: question })
    setLoading(true)
    setError(null)

    try {
      // Prefer the explicit movie title stamped from the URL; fall back to what
      // the sidebar auto-detected from message text.
      const movieName = movieTitle || movieContext?.titleKey || movieContext?.title || null
      const data = await chatAPI.sendMessage(question, sessionId, movieName)
      addMessage({
        role: 'assistant',
        content: data.answer || 'No response received.',
        sources: data.sources || [],
      })
    } catch (err) {
      addMessage({
        role: 'assistant',
        content: `⚠️ **Error**: ${err.message || 'Something went wrong. Please try again.'}`,
        sources: [],
      })
      setError(err.message)
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleNewChat = () => {
    clearChat()
    onNewChat?.()
    setTimeout(() => inputRef.current?.focus(), 100)
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex flex-col h-full bg-film-bg">
      {/* Top Bar */}
      <div className="flex items-center justify-between px-4 sm:px-6 py-3 border-b border-white/5 flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-sm font-medium text-film-subtle">FilmInsight AI</span>
          <span className="text-xs text-film-muted hidden sm:block">· Powered by Groq + RAG</span>
        </div>
        {!isEmpty && (
          <button
            onClick={handleNewChat}
            className="flex items-center gap-1.5 text-xs text-film-muted hover:text-white px-2.5 py-1.5 rounded-lg hover:bg-white/5 transition-all border border-white/5 hover:border-white/10"
          >
            <Plus size={13} />
            New Chat
          </button>
        )}
      </div>

      {/* Messages */}
      <div ref={messagesRef} className="flex-1 overflow-y-auto py-4 space-y-1 min-h-0">
        {isEmpty ? (
          /* Empty state */
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center h-full gap-6 px-4"
          >
            <div className="text-center">
              <div className="w-16 h-16 mx-auto rounded-2xl bg-red-gradient flex items-center justify-center mb-4 glow-red">
                <Film size={28} className="text-white" />
              </div>
              <h3 className="font-display font-bold text-xl text-white mb-1">
                What would you like to know?
              </h3>
              <p className="text-sm text-film-muted">
                Ask me anything about any movie — plot, characters, themes, quotes.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
              {STARTER_QUESTIONS.map(({ q, icon }) => (
                <button
                  key={q}
                  onClick={() => handleSend(q)}
                  className="glass border border-white/8 rounded-xl px-3 py-3 text-sm text-film-subtle hover:text-white hover:border-film-red/25 hover:bg-film-red/4 transition-all text-left flex items-start gap-2.5 group"
                >
                  <span className="text-base flex-shrink-0 group-hover:scale-110 transition-transform">{icon}</span>
                  <span className="leading-snug">{q}</span>
                </button>
              ))}
            </div>
          </motion.div>
        ) : (
          <>
            <AnimatePresence initial={false}>
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
            </AnimatePresence>
            {isLoading && <LoadingAnimation />}
          </>
        )}
        <div ref={endRef} />
      </div>

      {/* Input Bar */}
      <div className="flex-shrink-0 border-t border-white/5 p-3 sm:p-4">
        <div className={`flex items-end gap-2 glass border rounded-2xl transition-colors ${
          input ? 'border-film-red/35' : 'border-white/8'
        }`}>
          <textarea
            ref={inputRef}
            id="chat-input"
            rows={1}
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              // Auto-grow
              e.target.style.height = 'auto'
              e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px'
            }}
            onKeyDown={handleKeyDown}
            placeholder="Ask about a movie..."
            disabled={isLoading}
            className="flex-1 bg-transparent resize-none px-4 py-3.5 text-sm text-white placeholder-film-muted outline-none min-h-[52px] max-h-[160px] overflow-y-auto scrollbar-hide disabled:opacity-60"
          />
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="flex-shrink-0 mb-2 mr-2 w-9 h-9 rounded-xl bg-red-gradient flex items-center justify-center text-white disabled:opacity-35 disabled:cursor-not-allowed hover:opacity-90 transition-opacity"
          >
            {isLoading
              ? <RotateCcw size={15} className="animate-spin" />
              : <Send size={15} />
            }
          </motion.button>
        </div>

        <p className="text-center text-[11px] text-film-muted mt-2">
          <kbd className="px-1 py-0.5 rounded bg-white/5 font-mono">Enter</kbd> to send ·{' '}
          <kbd className="px-1 py-0.5 rounded bg-white/5 font-mono">Shift+Enter</kbd> for new line
        </p>
      </div>
    </div>
  )
}
