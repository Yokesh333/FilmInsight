import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Film, MessageCircle, Info, Zap, Menu, X, Sparkles, Home } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const navLinks = [
  { to: '/',        label: 'Home',     icon: Home },
  { to: '/features',label: 'Features', icon: Zap },
  { to: '/chat',    label: 'Chat',     icon: MessageCircle },
  { to: '/about',   label: 'About',    icon: Info },
]

export default function Navbar() {
  const location  = useLocation()
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const { user, logout } = useAuth()

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
        transition={{ duration: 0.55, ease: 'easeOut' }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
          scrolled
            ? 'bg-film-bg/80 backdrop-blur-2xl border-b border-white/5 shadow-glass'
            : 'bg-transparent'
        }`}
      >
        {/* Top accent line */}
        {scrolled && (
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-film-red/40 to-transparent" />
        )}

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="relative">
                <motion.div
                  whileHover={{ scale: 1.1, rotate: -5 }}
                  transition={{ type: 'spring', stiffness: 400 }}
                  className="w-8 h-8 rounded-xl bg-red-gradient flex items-center justify-center glow-red"
                >
                  <Film size={15} className="text-white" />
                </motion.div>
                <motion.div
                  animate={{ scale: [1, 1.3, 1], opacity: [0.7, 1, 0.7] }}
                  transition={{ duration: 2.5, repeat: Infinity }}
                  className="absolute -top-1 -right-1"
                >
                  <Sparkles size={9} className="text-film-gold" />
                </motion.div>
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
                    className={`relative px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                      active ? 'text-white' : 'text-film-muted hover:text-white'
                    }`}
                  >
                    {active && (
                      <motion.span
                        layoutId="nav-active"
                        className="absolute inset-0 glass border border-white/10 rounded-xl"
                        style={{ background: 'rgba(255,255,255,0.06)' }}
                        transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                      />
                    )}
                    <span className="relative z-10">{label}</span>
                  </Link>
                )
              })}
            </nav>

            {/* CTA */}
            <div className="hidden md:flex items-center gap-3">
              <Link to="/chat" className="btn-primary text-sm py-2 px-4 mr-2">
                <MessageCircle size={14} />
                Ask AI
              </Link>
              {user ? (
                <>
                  <Link to={user.role === 'admin' ? '/admin' : '/dashboard'} className="text-film-subtle hover:text-white text-sm font-medium transition-colors">
                    Dashboard
                  </Link>
                  <button onClick={logout} className="text-film-subtle hover:text-white text-sm font-medium transition-colors">
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" className="text-film-subtle hover:text-white text-sm font-medium transition-colors">
                    Login
                  </Link>
                  <Link to="/register" className="glass px-4 py-2 rounded-lg text-white text-sm font-medium transition-all hover:bg-white/10 border border-white/10">
                    Sign Up
                  </Link>
                </>
              )}
            </div>

            {/* Mobile toggle */}
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={() => setMenuOpen(!menuOpen)}
              className="md:hidden p-2 rounded-xl text-film-subtle hover:text-white hover:bg-white/5 transition-colors border border-white/5"
            >
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </motion.button>
          </div>
        </div>
      </motion.header>

      {/* Mobile Menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.22 }}
            className="fixed top-16 left-3 right-3 z-40 glass-strong border border-white/8 rounded-2xl shadow-glass md:hidden overflow-hidden"
          >
            <nav className="flex flex-col gap-1 p-3">
              {navLinks.map(({ to, label, icon: Icon }) => {
                const active = location.pathname === to
                return (
                  <Link
                    key={to}
                    to={to}
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                      active
                        ? 'bg-film-red/12 text-white border border-film-red/20'
                        : 'text-film-subtle hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <Icon size={16} className={active ? 'text-film-red' : ''} />
                    {label}
                  </Link>
                )
              })}
              <div className="pt-1 border-t border-white/6 mt-1 flex flex-col gap-2">
                {user ? (
                  <>
                    <Link to={user.role === 'admin' ? '/admin' : '/dashboard'} className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium text-film-subtle hover:text-white hover:bg-white/5 transition-all">
                      Dashboard
                    </Link>
                    <button onClick={logout} className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium text-film-subtle hover:text-white hover:bg-white/5 transition-all w-full">
                      Logout
                    </button>
                  </>
                ) : (
                  <>
                    <Link to="/login" className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium text-film-subtle hover:text-white hover:bg-white/5 transition-all">
                      Login
                    </Link>
                    <Link to="/register" className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium glass border border-white/10 text-white transition-all hover:bg-white/10">
                      Sign Up
                    </Link>
                  </>
                )}
                <Link to="/chat" className="btn-primary w-full justify-center text-sm py-2.5 mt-2">
                  <MessageCircle size={15} />
                  Ask AI Now
                </Link>
              </div>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
