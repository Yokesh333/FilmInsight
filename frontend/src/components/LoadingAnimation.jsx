import { motion } from 'framer-motion'

export default function LoadingAnimation() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="flex items-start gap-3 px-4 py-3"
    >
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-red-gradient flex items-center justify-center shadow-glow-red-sm">
        <span className="text-[10px] font-bold text-white">✦</span>
      </div>

      {/* Bubble */}
      <div className="glass-card border border-white/8 rounded-2xl rounded-tl-sm px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="typing-dot" />
          <div className="typing-dot" />
          <div className="typing-dot" />
          <span className="ml-1 text-xs text-film-muted font-medium">FilmInsight is thinking…</span>
        </div>
      </div>
    </motion.div>
  )
}
