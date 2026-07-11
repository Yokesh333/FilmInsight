import { motion } from 'framer-motion'
import { Github, Linkedin, ExternalLink } from 'lucide-react'

export default function About() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="pt-24 pb-16 px-4"
    >
      <div className="max-w-5xl mx-auto">
        {/* Hero */}
        <div className="text-center mb-16">
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-xs font-semibold uppercase tracking-widest text-film-red mb-3"
          >
            About the Project
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="font-display font-black text-4xl sm:text-5xl text-white mb-4"
          >
            Meet <span className="gradient-text">FilmInsight</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-film-subtle max-w-2xl mx-auto leading-relaxed"
          >
            FilmInsight is an AI-powered movie assistant built as part of an M.Tech research project
            exploring the intersection of large language models, semantic search, and cinematic knowledge.
          </motion.p>
        </div>

        {/* Author Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="glass border border-white/8 rounded-3xl p-8 mb-12 flex flex-col sm:flex-row gap-6 items-center sm:items-start"
        >
          <div className="flex-shrink-0 w-20 h-20 rounded-2xl bg-gradient-to-br from-film-red to-orange-600 flex items-center justify-center text-2xl font-black text-white font-display">
            YD
          </div>
          <div className="flex-1 text-center sm:text-left">
            <h2 className="font-display font-bold text-xl text-white mb-1">Yokesh D</h2>
            <p className="text-film-red text-sm font-medium mb-1">M.Tech Integrated — Software Engineering</p>
            <p className="text-film-muted text-sm mb-3">Vellore Institute of Technology, Vellore</p>
            <p className="text-film-subtle text-sm leading-relaxed max-w-lg">
              Passionate about AI, full-stack development, and building production-ready systems
              that combine cutting-edge ML with intuitive user experiences.
            </p>
            <div className="flex gap-3 mt-4 justify-center sm:justify-start">
              <a href="https://github.com/Yokesh333" target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 glass border border-white/10 rounded-lg text-xs text-film-subtle hover:text-white transition-colors">
                <Github size={14} /> GitHub
              </a>
              <a href="#" target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 glass border border-white/10 rounded-lg text-xs text-film-subtle hover:text-white transition-colors">
                <Linkedin size={14} /> LinkedIn
              </a>
            </div>
          </div>
        </motion.div>

        {/* Repo CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center"
        >
          <a
            href="https://github.com/Yokesh333/FilmInsight"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2.5 px-7 py-3.5 glass border border-white/15 rounded-xl font-semibold text-film-subtle hover:text-white hover:border-white/25 transition-all hover:scale-105"
          >
            <Github size={18} />
            View on GitHub
            <ExternalLink size={14} />
          </a>
        </motion.div>
      </div>
    </motion.div>
  )
}
