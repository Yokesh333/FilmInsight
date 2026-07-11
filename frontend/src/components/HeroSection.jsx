import { useRef } from 'react'
import { Link } from 'react-router-dom'
import { motion, useScroll, useTransform } from 'framer-motion'
import { MessageCircle, Upload, Sparkles, ChevronDown, Play } from 'lucide-react'

const FEATURED_MOVIES = [
  { title: '500 Days of Summer', genre: 'Romance · Drama',  year: 2009, rating: '7.7' },
  { title: 'Inception',          genre: 'Sci-Fi · Thriller',year: 2010, rating: '8.8' },
  { title: 'Interstellar',       genre: 'Sci-Fi · Drama',  year: 2014, rating: '8.7' },
  { title: 'The Dark Knight',    genre: 'Action · Crime',  year: 2008, rating: '9.0' },
  { title: 'Parasite',           genre: 'Drama · Thriller',year: 2019, rating: '8.5' },
]

const GRADIENT_COLORS = [
  'from-red-900/60 to-orange-900/40',
  'from-blue-900/60 to-indigo-900/40',
  'from-amber-900/60 to-yellow-900/40',
  'from-gray-900/60 to-slate-800/40',
  'from-green-900/60 to-teal-900/40',
]

function FloatingBadge({ children, className }) {
  return (
    <motion.div
      animate={{ y: [0, -8, 0] }}
      transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
      className={`glass border border-white/10 rounded-2xl px-3 py-2 text-xs text-film-subtle absolute ${className}`}
    >
      {children}
    </motion.div>
  )
}

export default function HeroSection() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({ target: ref })
  const y = useTransform(scrollYProgress, [0, 1], ['0%', '30%'])

  return (
    <section ref={ref} className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden hero-scanline noise">
      {/* Ambient background orbs */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-film-red/8 rounded-full blur-3xl" />
        <div className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-blue-900/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-film-red/3 rounded-full blur-3xl" />
      </div>

      {/* Grid dots */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.8) 1px, transparent 1px)',
          backgroundSize: '32px 32px',
        }}
      />

      {/* Floating UI hints */}
      <FloatingBadge className="top-36 left-10 hidden xl:block" >
        🎬 500 Days of Summer loaded
      </FloatingBadge>
      <FloatingBadge className="top-48 right-16 hidden xl:block" style={{ animationDelay: '1.2s' }}>
        ✨ RAG-powered answers
      </FloatingBadge>
      <FloatingBadge className="bottom-40 left-16 hidden xl:block" style={{ animationDelay: '2s' }}>
        ⚡ Groq LLM inference
      </FloatingBadge>

      {/* Main content */}
      <motion.div style={{ y }} className="relative z-10 text-center px-4 max-w-5xl mx-auto">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 glass border border-film-red/25 rounded-full px-4 py-1.5 mb-6 text-xs font-medium text-film-subtle"
        >
          <Sparkles size={12} className="text-film-red" />
          Powered by RAG + Groq + Chroma
          <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="font-display font-black text-5xl sm:text-6xl lg:text-7xl xl:text-8xl leading-none mb-6"
        >
          <span className="block text-white">Your AI</span>
          <span className="block gradient-text">Movie Expert</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="text-film-subtle text-lg sm:text-xl max-w-2xl mx-auto leading-relaxed mb-10"
        >
          Upload any movie screenplay and ask anything — characters, plot, themes, quotes,
          trivia — powered by Retrieval-Augmented Generation.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center"
        >
          <Link
            to="/chat"
            className="group flex items-center gap-2.5 px-7 py-3.5 bg-red-gradient rounded-xl font-semibold text-white text-sm glow-red hover:opacity-90 hover:scale-105 transition-all duration-300"
          >
            <MessageCircle size={18} />
            Start Chatting
            <span className="group-hover:translate-x-1 transition-transform">→</span>
          </Link>
          <Link
            to="/features"
            className="flex items-center gap-2.5 px-7 py-3.5 glass border border-white/10 rounded-xl font-semibold text-film-subtle text-sm hover:text-white hover:border-white/20 hover:bg-white/5 transition-all duration-300"
          >
            <Play size={16} />
            See Features
          </Link>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.55 }}
          className="flex items-center justify-center gap-8 mt-14 flex-wrap"
        >
          {[
            { value: 'RAG',  label: 'Retrieval Engine' },
            { value: 'PDF',  label: 'Screenplay Upload' },
            { value: 'LLM',  label: 'Groq Inference' },
            { value: '∞',    label: 'Questions' },
          ].map(({ value, label }) => (
            <div key={label} className="text-center">
              <p className="font-display font-bold text-2xl gradient-text">{value}</p>
              <p className="text-film-muted text-xs mt-0.5">{label}</p>
            </div>
          ))}
        </motion.div>
      </motion.div>

      {/* Featured Movies Row */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.7 }}
        className="relative z-10 w-full max-w-6xl mx-auto px-4 mt-20"
      >
        <p className="text-center text-film-muted text-xs uppercase tracking-widest mb-5">
          Works with any screenplay
        </p>
        <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide justify-center flex-wrap sm:flex-nowrap">
          {FEATURED_MOVIES.map((movie, i) => (
            <motion.div
              key={movie.title}
              whileHover={{ y: -6, scale: 1.02 }}
              className={`flex-shrink-0 w-40 sm:w-44 rounded-2xl bg-gradient-to-br ${GRADIENT_COLORS[i]} border border-white/8 p-4 cursor-pointer transition-shadow hover:shadow-card`}
            >
              <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center mb-3">
                <span className="text-lg">🎬</span>
              </div>
              <p className="font-display font-semibold text-sm text-white leading-tight mb-1">{movie.title}</p>
              <p className="text-xs text-film-muted mb-1">{movie.genre}</p>
              <div className="flex items-center gap-1">
                <span className="text-film-gold text-xs">★</span>
                <span className="text-xs text-film-subtle">{movie.rating}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Scroll hint */}
      <motion.div
        animate={{ y: [0, 6, 0] }}
        transition={{ duration: 2, repeat: Infinity }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 text-film-muted flex flex-col items-center gap-1"
      >
        <span className="text-xs">Scroll to explore</span>
        <ChevronDown size={16} />
      </motion.div>
    </section>
  )
}
