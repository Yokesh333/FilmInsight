import { motion } from 'framer-motion'
import { Users } from 'lucide-react'

const DEFAULT_CAST = [
  { name: 'Joseph Gordon-Levitt', role: 'Tom Hansen' },
  { name: 'Zooey Deschanel',      role: 'Summer Finn' },
  { name: 'Geoffrey Arend',       role: 'McKenzie' },
  { name: 'Chloe Grace Moretz',   role: 'Rachel Hansen' },
]

const AVATAR_COLORS = [
  'from-blue-600 to-indigo-700',
  'from-pink-600 to-rose-700',
  'from-emerald-600 to-teal-700',
  'from-amber-600 to-orange-700',
  'from-purple-600 to-violet-700',
  'from-red-600 to-rose-700',
  'from-cyan-600 to-blue-700',
  'from-lime-600 to-green-700',
]

export default function CastCard({ cast }) {
  const members = cast || DEFAULT_CAST

  return (
    <div className="glass border border-white/8 rounded-2xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-6 h-6 rounded-lg bg-blue-500/15 flex items-center justify-center">
          <Users size={13} className="text-blue-400" />
        </div>
        <h4 className="text-xs font-semibold uppercase tracking-wider text-film-subtle">Cast</h4>
        <span className="text-[10px] text-film-muted ml-auto">{members.length} members</span>
      </div>

      <div className="space-y-2">
        {members.map((member, i) => (
          <motion.div
            key={member.name}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.06 }}
            className="flex items-center gap-3 p-2 rounded-xl hover:bg-white/3 transition-colors"
          >
            {/* Avatar */}
            <div className={`flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br ${AVATAR_COLORS[i % AVATAR_COLORS.length]} flex items-center justify-center text-white text-xs font-bold`}>
              {member.name.split(' ').map(w => w[0]).join('').slice(0, 2)}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-white truncate">{member.name}</p>
              {member.role && (
                <p className="text-xs text-film-red truncate">as {member.role}</p>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
