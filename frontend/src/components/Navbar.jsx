import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Film, MessageCircle, Info, Zap, Menu, X, Sparkles } from 'lucide-react'

const navLinks = [
  { to: '/',        label: 'Home',     icon: Film },
  { to: '/features',label: 'Features', icon: Zap },
  { to: '/chat',    label: 'Chat',     icon: MessageCircle },
  { to: '/about',   label: 'About',    icon: Info },
]

export default function Navbar() {
  const location  = useLocation()
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => { setMenuOpen(false) }, [location])

  return (
    <>
      <motion.header
        initial={{ y: -80, opacity: 0 }}
        animate={{ y: 0,   opacity: 1 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
          scrolled
            ? 'bg-film-bg/90 backdrop-blur-xl border-b border-white/5 shadow-glass'
            : 'bg-transparent'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="relative">
                <div className="w-8 h-8 rounded-lg bg-red-gradient flex items-center justify-center glow-red group-hover:scale-110 transition-transform duration-300">
                  <Film size={16} className="text-white" />
                </div>
                <Sparkles size={10} className="absolute -top-1 -right-1 text-film-gold animate-pulse" />
              </div>
              <span className="font-display font-bold text-xl">
                <span className="gradient-text">Film</span>
                <span className="text-white">Insight</span>
              </span>
            </Link>

            {/* Desktop Nav */}
            <nav className="hidden md:flex items-center gap-1">
              {navLinks.map(({ to, label }) => {
                const active = location.pathname === to
                return (
                  <Link
                    key={to}
                    to={to}
                    className={`relative px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                      active
                        ? 'text-white'
                        : 'text-film-muted hover:text-white hover:bg-white/5'
                    }`}
                  >
                    {active && (
                      <motion.span
                        layoutId="nav-pill"
                        className="absolute inset-0 bg-white/8 rounded-lg border border-white/10"
                        transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                      />
                    )}
                    <span className="relative z-10">{label}</span>
                  </Link>
                )
              })}
            </nav>

            {/* CTA */}
            <div className="hidden md:flex items-center gap-3">
              <Link
                to="/chat"
                className="flex items-center gap-2 px-4 py-2 bg-red-gradient rounded-lg text-sm font-semibold text-white glow-red hover:opacity-90 hover:scale-105 transition-all duration-300"
              >
                <MessageCircle size={15} />
                Ask AI
              </Link>
            </div>

            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="md:hidden p-2 rounded-lg text-film-subtle hover:text-white hover:bg-white/5 transition-colors"
              aria-label="Toggle menu"
            >
              {menuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>
      </motion.header>

      {/* Mobile Menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25 }}
            className="fixed top-16 left-0 right-0 z-40 glass-strong border-b border-white/5 md:hidden"
          >
            <nav className="flex flex-col gap-1 p-4">
              {navLinks.map(({ to, label, icon: Icon }) => {
                const active = location.pathname === to
                return (
                  <Link
                    key={to}
                    to={to}
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                      active
                        ? 'bg-film-red/15 text-film-red border border-film-red/20'
                        : 'text-film-subtle hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <Icon size={17} />
                    {label}
                  </Link>
                )
              })}
              <Link
                to="/chat"
                className="mt-2 flex items-center justify-center gap-2 px-4 py-3 bg-red-gradient rounded-xl text-sm font-semibold text-white"
              >
                <MessageCircle size={16} />
                Ask AI Now
              </Link>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
