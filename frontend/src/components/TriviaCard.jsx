import { motion } from 'framer-motion'
import { Lightbulb, Sparkles } from 'lucide-react'

const TRIVIA_ITEMS = [
  { fact: 'The film uses a non-linear narrative structure, jumping between days non-sequentially.', tag: 'Narrative' },
  { fact: 'Joseph Gordon-Levitt has stated the film is about how we idealize people we fall for.', tag: 'Themes' },
  { fact: 'The film was shot in just 34 days on a budget of $7.5 million.', tag: 'Production' },
  { fact: 'Zooey Deschanel\'s character Summer never says she loves Tom.', tag: 'Character' },
]

export default function TriviaCard({ trivia }) {
  const items = trivia || TRIVIA_ITEMS

  return (
    <div className="glass border border-white/8 rounded-2xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-6 h-6 rounded-lg bg-film-gold/15 flex items-center justify-center">
          <Lightbulb size={13} className="text-film-gold" />
        </div>
        <h4 className="text-xs font-semibold uppercase tracking-wider text-film-subtle">Movie Trivia</h4>
      </div>

      <div className="space-y-2.5">
        {items.map((item, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className="flex items-start gap-2.5 p-2.5 rounded-xl hover:bg-white/3 transition-colors"
          >
            <Sparkles size={12} className="text-film-gold flex-shrink-0 mt-0.5" />
            <div className="min-w-0">
              <p className="text-xs text-film-subtle leading-relaxed">{item.fact}</p>
              {item.tag && (
                <span className="inline-block mt-1 text-xs px-1.5 py-0.5 rounded-md bg-film-gold/10 text-film-gold/70 border border-film-gold/15">
                  {item.tag}
                </span>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
