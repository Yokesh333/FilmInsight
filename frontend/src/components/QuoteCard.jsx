import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Quote, ChevronLeft, ChevronRight } from 'lucide-react'

const DEFAULT_QUOTES = [
  { text: "I'm not easy to understand, Tom. And you can't figure me out by watching me walk.", speaker: 'Summer Finn' },
  { text: "Most days of the year are unremarkable, they begin and they end with no lasting memory.", speaker: 'Narrator' },
  { text: "I love how she makes me feel, like anything's possible, or like life is worth it.", speaker: 'Tom Hansen' },
  { text: "I just... I just woke up one day and I knew. Knew what I was never sure of with you.", speaker: 'Summer Finn' },
]

export default function QuoteCard({ quotes }) {
  const items = quotes || DEFAULT_QUOTES
  const [idx, setIdx] = useState(0)

  const prev = () => setIdx((i) => (i - 1 + items.length) % items.length)
  const next = () => setIdx((i) => (i + 1) % items.length)

  const quote = items[idx]

  return (
    <div className="glass border border-white/8 rounded-2xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-6 h-6 rounded-lg bg-film-red/15 flex items-center justify-center">
          <Quote size={13} className="text-film-red" />
        </div>
        <h4 className="text-xs font-semibold uppercase tracking-wider text-film-subtle">Famous Quotes</h4>
      </div>

      <div className="relative min-h-[80px] flex flex-col justify-between">
        <AnimatePresence mode="wait">
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
          >
            <p className="text-sm text-film-subtle italic leading-relaxed mb-2">
              "{quote.text}"
            </p>
            <p className="text-xs font-semibold text-film-red">— {quote.speaker}</p>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-white/5">
        <button
          onClick={prev}
          className="p-1.5 rounded-lg hover:bg-white/5 text-film-muted hover:text-white transition-colors"
        >
          <ChevronLeft size={15} />
        </button>
        <div className="flex gap-1.5">
          {items.map((_, i) => (
            <button
              key={i}
              onClick={() => setIdx(i)}
              className={`w-1.5 h-1.5 rounded-full transition-all ${
                i === idx ? 'bg-film-red w-3' : 'bg-white/20'
              }`}
            />
          ))}
        </div>
        <button
          onClick={next}
          className="p-1.5 rounded-lg hover:bg-white/5 text-film-muted hover:text-white transition-colors"
        >
          <ChevronRight size={15} />
        </button>
      </div>
    </div>
  )
}
