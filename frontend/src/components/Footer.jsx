import { Link } from 'react-router-dom'
import { Film, Github, Twitter, Linkedin, Heart, ExternalLink } from 'lucide-react'

const links = {
  Product: [
    { label: 'Home',     to: '/' },
    { label: 'Chat',     to: '/chat' },
    { label: 'Features', to: '/features' },
    { label: 'About',    to: '/about' },
  ],
  Tech: [
    { label: 'Flowise',       href: 'https://flowiseai.com' },
    { label: 'Groq LLM',      href: 'https://groq.com' },
    { label: 'HuggingFace',   href: 'https://huggingface.co' },
    { label: 'Chroma DB',     href: 'https://trychroma.com' },
  ],
}

const socials = [
  { icon: Github,   href: 'https://github.com/Yokesh333/FilmInsight', label: 'GitHub' },
  { icon: Twitter,  href: '#', label: 'Twitter' },
  { icon: Linkedin, href: '#', label: 'LinkedIn' },
]

export default function Footer() {
  return (
    <footer className="relative bg-film-surface border-t border-white/5 mt-auto">
      {/* Gradient top border */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-film-red/40 to-transparent" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Brand */}
          <div className="md:col-span-2">
            <Link to="/" className="flex items-center gap-2.5 mb-4">
              <div className="w-8 h-8 rounded-lg bg-red-gradient flex items-center justify-center">
                <Film size={16} className="text-white" />
              </div>
              <span className="font-display font-bold text-xl">
                <span className="gradient-text">Film</span>
                <span className="text-white">Insight</span>
              </span>
            </Link>
            <p className="text-film-muted text-sm leading-relaxed max-w-xs">
              AI-powered movie assistant using Retrieval-Augmented Generation.
              Ask anything about your favorite films and screenplays.
            </p>
            <div className="flex items-center gap-3 mt-5">
              {socials.map(({ icon: Icon, href, label }) => (
                <a
                  key={label}
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={label}
                  className="w-9 h-9 rounded-lg glass flex items-center justify-center text-film-muted hover:text-white hover:border-white/15 transition-all duration-300 hover:scale-110"
                >
                  <Icon size={16} />
                </a>
              ))}
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(links).map(([section, items]) => (
            <div key={section}>
              <h3 className="text-xs font-semibold uppercase tracking-widest text-film-muted mb-4">{section}</h3>
              <ul className="space-y-2.5">
                {items.map((item) => (
                  <li key={item.label}>
                    {'to' in item ? (
                      <Link to={item.to} className="text-sm text-film-subtle hover:text-white transition-colors flex items-center gap-1 group">
                        {item.label}
                      </Link>
                    ) : (
                      <a href={item.href} target="_blank" rel="noopener noreferrer" className="text-sm text-film-subtle hover:text-white transition-colors flex items-center gap-1 group">
                        {item.label}
                        <ExternalLink size={11} className="opacity-0 group-hover:opacity-60 transition-opacity" />
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="border-t border-white/5 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-film-muted text-xs">
            © {new Date().getFullYear()} FilmInsight. Built by{' '}
            <span className="text-film-subtle font-medium">Yokesh D</span> · VIT Chennai
          </p>
          <p className="text-film-muted text-xs flex items-center gap-1">
            Made with <Heart size={11} className="text-film-red animate-pulse" fill="currentColor" /> using RAG + Groq
          </p>
        </div>
      </div>
    </footer>
  )
}
