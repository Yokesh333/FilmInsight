import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Film, Star, Play, Heart, AlertCircle } from 'lucide-react'

export default function MovieCard({ movie, onClick, index, isFavorite, onToggleFavorite }) {
  const [hovered,     setHovered]     = useState(false)
  const [imgLoaded,   setImgLoaded]   = useState(false)
  const [imgError,    setImgError]    = useState(false)

  const hasPoster = movie.poster && !imgError

  const handleFavoriteClick = (e) => {
    e.stopPropagation()
    if (onToggleFavorite) {
      onToggleFavorite(movie)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index !== undefined ? index * 0.07 : 0, duration: 0.5 }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => { console.log('[TRACE][0] MovieCard clicked', { title: movie.title, status: movie.status, id: movie.id }); onClick(movie) }}
      className="cursor-pointer group"
    >
      {/* Poster */}
      <div
        className="relative rounded-2xl overflow-hidden mb-3 border border-white/5 group-hover:border-white/20 transition-all duration-300 bg-film-surface"
        style={{
          aspectRatio: '2/3',
          boxShadow: hovered ? `0 20px 60px rgba(0,0,0,0.5)` : '0 4px 24px rgba(0,0,0,0.3)',
          transform: hovered ? 'scale(1.03) translateY(-4px)' : 'scale(1) translateY(0)',
          transition: 'transform 0.35s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.35s ease, border-color 0.3s ease',
        }}
      >
        {/* Real TMDB poster image */}
        {hasPoster ? (
          <>
            {!imgLoaded && (
              <div className="absolute inset-0 bg-gradient-to-b from-film-surface to-film-bg animate-pulse" />
            )}
            <img
              src={movie.poster || movie.poster_url}
              alt={movie.title || movie.movie_title}
              loading="lazy"
              onLoad={() => setImgLoaded(true)}
              onError={() => setImgError(true)}
              className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-500 ${imgLoaded ? 'opacity-100' : 'opacity-0'}`}
            />
          </>
        ) : (
          /* Fallback gradient with film icon */
          <div className="absolute inset-0 bg-gradient-to-b from-film-surface to-film-bg flex items-center justify-center">
            <Film size={40} className="text-white/10" />
          </div>
        )}

        {/* Gradient overlay always on top */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/10 to-transparent" />

        {/* Hover red glow overlay */}
        <div
          className="absolute inset-0 transition-opacity duration-300"
          style={{ background: 'radial-gradient(circle at 50% 100%, rgba(229,9,20,0.15) 0%, transparent 70%)', opacity: hovered ? 1 : 0 }}
        />

        {/* Favorite Heart */}
        {onToggleFavorite && (
          <button 
            onClick={handleFavoriteClick}
            className="absolute top-2.5 left-2.5 z-10 p-1.5 rounded-full bg-black/50 backdrop-blur-sm border border-white/10 hover:bg-black/80 transition-colors"
          >
            <Heart 
              size={16} 
              className={isFavorite ? 'text-red-500 fill-red-500' : 'text-white'} 
            />
          </button>
        )}

        {/* Rating badge */}
        {movie.rating && (
            <div className="absolute top-2.5 right-2.5 flex items-center gap-1 px-2 py-1 bg-black/75 backdrop-blur-sm rounded-full border border-white/10">
            <Star size={10} className="text-yellow-400 fill-yellow-400 flex-shrink-0" />
            <span className="text-xs font-bold text-white">{movie.rating}</span>
            </div>
        )}

        {/* Year badge */}
        {(movie.year || movie.movie_year) && (
            <div className={`absolute ${movie.rating || onToggleFavorite ? 'bottom-2.5 left-2.5' : 'top-2.5 left-2.5'} px-2 py-0.5 bg-black/65 backdrop-blur-sm rounded-full border border-white/10`}>
            <span className="text-[10px] font-medium text-film-subtle">{movie.year || movie.movie_year}</span>
            </div>
        )}

        {/* Script badge */}
        {movie.has_script && (
          <div className="absolute bottom-10 left-2.5 px-2 py-0.5 bg-film-red/80 backdrop-blur-sm rounded-full">
            <span className="text-[9px] font-bold text-white uppercase tracking-wider">Script</span>
          </div>
        )}

        {/* Failed Status Overlay */}
        {movie.status === 'FAILED' && (
          <div className="absolute inset-0 bg-red-900/80 backdrop-blur-sm flex flex-col items-center justify-center p-4 text-center z-20">
            <AlertCircle size={24} className="text-white mb-2" />
            <p className="text-white font-bold text-xs">Embedding failed.</p>
            <p className="text-white/80 text-[10px] mt-1">Retry ingestion.</p>
          </div>
        )}

        {/* Hover CTA */}
        <AnimatePresence>
          {hovered && (!movie.status || movie.status === 'READY') && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.2 }}
              className="absolute bottom-3 right-3 flex justify-center"
            >
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-red-gradient rounded-full text-xs font-semibold text-white shadow-button">
                <Play size={10} fill="white" />
                Ask AI
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Info */}
      <motion.h3
        animate={{ color: hovered ? '#E50914' : '#ffffff' }}
        transition={{ duration: 0.2 }}
        className="font-display font-bold text-sm leading-tight mb-0.5"
      >
        {movie.title || movie.movie_title}
      </motion.h3>
      {movie.overview && <p className="text-xs text-film-muted">{movie.overview.slice(0, 60) + '…'}</p>}
    </motion.div>
  )
}
