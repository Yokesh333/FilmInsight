import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Film, Star, Calendar, Clock, ChevronDown, ChevronUp, Info, Users, Award } from 'lucide-react'

// Demo data for 500 Days of Summer
const DEFAULT_MOVIE = {
  title:    '500 Days of Summer',
  year:     2009,
  rating:   7.7,
  runtime:  '1h 35m',
  genre:    ['Romance', 'Comedy', 'Drama'],
  director: 'Marc Webb',
  cast:     ['Joseph Gordon-Levitt', 'Zooey Deschanel', 'Geoffrey Arend'],
  plot:     'A hopeful romantic who falls head over heels for an enchanting young woman who does not believe in love.',
  awards:   'Independent Spirit Award nomination',
  status:   'loaded',
}

export default function MovieDetailsCard({ movie = DEFAULT_MOVIE }) {
  const [expanded, setExpanded] = useState(false)

  const stars = Math.round(movie.rating / 2)

  return (
    <motion.div
      initial={{ opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4 }}
      className="glass border border-white/8 rounded-2xl overflow-hidden"
    >
      {/* Movie Banner */}
      <div className="relative h-24 bg-gradient-to-br from-blue-900/60 via-indigo-900/40 to-film-bg flex items-center justify-center">
        <Film size={32} className="text-white/20" />
        {/* Status badge */}
        <span className={`absolute top-3 right-3 text-xs px-2 py-0.5 rounded-full font-medium ${
          movie.status === 'loaded'
            ? 'bg-green-500/20 text-green-400 border border-green-500/30'
            : 'bg-film-muted/20 text-film-muted border border-white/10'
        }`}>
          {movie.status === 'loaded' ? '✓ Loaded' : 'Not loaded'}
        </span>
        <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-film-card to-transparent" />
      </div>

      <div className="p-4">
        {/* Title */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div>
            <h3 className="font-display font-bold text-white text-sm leading-tight">{movie.title}</h3>
            <div className="flex items-center gap-2 mt-1">
              <Calendar size={11} className="text-film-muted" />
              <span className="text-xs text-film-muted">{movie.year}</span>
              <Clock size={11} className="text-film-muted" />
              <span className="text-xs text-film-muted">{movie.runtime}</span>
            </div>
          </div>
          <div className="flex items-center gap-1 flex-shrink-0">
            <Star size={13} className="text-film-gold" fill="currentColor" />
            <span className="text-sm font-bold text-film-gold">{movie.rating}</span>
            <span className="text-xs text-film-muted">/10</span>
          </div>
        </div>

        {/* Stars */}
        <div className="flex gap-0.5 mb-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Star
              key={i}
              size={12}
              className={i < stars ? 'text-film-gold' : 'text-white/10'}
              fill={i < stars ? 'currentColor' : 'none'}
            />
          ))}
        </div>

        {/* Genre Tags */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          {movie.genre.map((g) => (
            <span key={g} className="text-xs px-2 py-0.5 rounded-full glass border border-white/8 text-film-subtle">
              {g}
            </span>
          ))}
        </div>

        {/* Expand toggle */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-between text-xs text-film-muted hover:text-white transition-colors py-1"
        >
          <span>More details</span>
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>

        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="pt-3 space-y-2.5 border-t border-white/5 mt-2">
                <div className="flex items-start gap-2">
                  <Info size={13} className="text-film-red flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-film-subtle leading-relaxed">{movie.plot}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Users size={13} className="text-film-muted flex-shrink-0" />
                  <p className="text-xs text-film-subtle">{movie.cast.join(', ')}</p>
                </div>
                {movie.awards && (
                  <div className="flex items-center gap-2">
                    <Award size={13} className="text-film-gold flex-shrink-0" />
                    <p className="text-xs text-film-subtle">{movie.awards}</p>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
