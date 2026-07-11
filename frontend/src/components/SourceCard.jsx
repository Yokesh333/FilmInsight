import { motion } from 'framer-motion'
import { FileText, ExternalLink, Hash } from 'lucide-react'

export default function SourceCard({ source, index }) {
  const { pageLabel, content, page, score } = source || {}

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.08 }}
      className="glass border border-white/8 rounded-xl p-3 hover:border-film-red/25 transition-all group cursor-pointer"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-film-red/15 flex items-center justify-center">
            <FileText size={12} className="text-film-red" />
          </div>
          <div>
            <p className="text-xs font-semibold text-white">{pageLabel || `Source ${index + 1}`}</p>
            {page !== undefined && (
              <div className="flex items-center gap-1">
                <Hash size={9} className="text-film-muted" />
                <span className="text-xs text-film-muted">Page {page}</span>
              </div>
            )}
          </div>
        </div>
        {score !== undefined && (
          <span className="text-xs px-1.5 py-0.5 rounded-full glass border border-green-500/20 text-green-400">
            {Math.round(score * 100)}%
          </span>
        )}
      </div>

      {content && (
        <p className="text-xs text-film-muted leading-relaxed line-clamp-3 group-hover:text-film-subtle transition-colors">
          "{content}"
        </p>
      )}
    </motion.div>
  )
}
