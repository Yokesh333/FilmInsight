import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Film, Github, Twitter, Linkedin, Heart, ExternalLink, Zap } from 'lucide-react'

const links = {
  Product: [
    { label: 'Home',     to: '/' },
    { label: 'Chat',     to: '/chat' },
    { label: 'Features', to: '/features' },
    { label: 'About',    to: '/about' },
  ],
  Tech: [
    { label: 'Flowise',      href: 'https://flowiseai.com' },
    { label: 'Groq LLM',     href: 'https://groq.com' },
    { label: 'HuggingFace',  href: 'https://huggingface.co' },
    { label: 'ChromaDB',     href: 'https://trychroma.com' },
  ],
}

const socials = [
  { icon: Github,   href: 'https://github.com/Yokesh333/FilmInsight', label: 'GitHub' },
  { icon: Twitter,  href: '#', label: 'Twitter' },
  { icon: Linkedin, href: '#', label: 'LinkedIn' },
]

export default function Footer() {
  return (
    <footer className="relative bg-film-surface/60 backdrop-blur-xl border-t border-white/5 mt-auto">
      {/* Gradient top border */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-film-red/35 to-transparent" />
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-96 h-32 bg-film-red/4 rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Brand */}
          <div className="md:col-span-2">
            <Link to="/" className="flex items-center gap-2.5 mb-4 group w-fit">
              <motion.div
                whileHover={{ scale: 1.1, rotate: -5 }}
                className="w-8 h-8 rounded-xl bg-red-gradient flex items-center justify-center glow-red"
              >
                <Film size={15} className="text-white" />
              </motion.div>
              <span className="font-display font-bold text-xl">
                <span className="gradient-text">Film</span>
                <span className="text-white">Insight</span>
              </span>
            </Link>

            <p className="text-film-muted text-sm leading-relaxed max-w-xs mb-5">
              AI-powered movie assistant using Retrieval-Augmented Generation.
              Ask anything about your favorite films and screenplays.
            </p>

            {/* Status */}
            <div className="flex items-center gap-2 mb-5">
              <div className="badge badge-green">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                AI Online
              </div>
              <div className="badge badge-red">
                <Zap size={9} />
                Groq Powered
              </div>
            </div>

            <div className="flex items-center gap-2">
              {socials.map(({ icon: Icon, href, label }) => (
                <motion.a
                  key={label}
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={label}
                  whileHover={{ scale: 1.12, y: -2 }}
                  whileTap={{ scale: 0.93 }}
                  className="w-9 h-9 rounded-xl glass border border-white/8 flex items-center justify-center text-film-muted hover:text-white hover:border-white/18 transition-colors duration-200"
                >
                  <Icon size={15} />
                </motion.a>
              ))}
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(links).map(([section, items]) => (
            <div key={section}>
              <h3 className="text-[10px] font-semibold uppercase tracking-widest text-film-muted mb-4">{section}</h3>
              <ul className="space-y-2.5">
                {items.map((item) => (
                  <li key={item.label}>
                    {'to' in item ? (
                      <Link to={item.to}
                        className="text-sm text-film-subtle hover:text-white transition-colors duration-200 flex items-center gap-1 group">
                        <span className="w-0 h-px bg-film-red transition-all duration-200 group-hover:w-3" />
                        {item.label}
                      </Link>
                    ) : (
                      <a href={item.href} target="_blank" rel="noopener noreferrer"
                        className="text-sm text-film-subtle hover:text-white transition-colors duration-200 flex items-center gap-1 group">
                        <span className="w-0 h-px bg-film-red transition-all duration-200 group-hover:w-3" />
                        {item.label}
                        <ExternalLink size={10} className="opacity-0 group-hover:opacity-50 transition-opacity" />
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="border-t border-white/5 pt-5 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-film-muted text-xs">
            © {new Date().getFullYear()} FilmInsight. Built by{' '}
            <span className="text-film-subtle font-medium">Yokesh D</span>{' '}
            · VIT Vellore
          </p>
          <p className="text-film-muted text-xs flex items-center gap-1.5">
            Made with <Heart size={11} className="text-film-red animate-pulse" fill="currentColor" /> using RAG + Groq LLaMA 3
          </p>
        </div>
      </div>
    </footer>
  )
}
