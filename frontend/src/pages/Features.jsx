import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  Brain, Upload, Search, MessageCircle, Zap, Shield,
  Database, FileText, Users, Quote, Lightbulb, Globe,
  ChevronRight, CheckCircle2,
} from 'lucide-react'

const ALL_FEATURES = [
  {
    icon: Upload,      color: 'text-blue-400',   bg: 'bg-blue-500/10',
    title: 'PDF Screenplay Upload',
    desc:  'Drag and drop any movie screenplay PDF. The system automatically chunks, embeds, and indexes it into Chroma for lightning-fast retrieval.',
    badges: ['Chroma Vector DB', 'Auto Chunking', 'HuggingFace Embeddings'],
  },
  {
    icon: Brain,       color: 'text-film-red',    bg: 'bg-film-red/10',
    title: 'Retrieval-Augmented Generation',
    desc:  'Every answer is grounded in actual screenplay content. FilmInsight retrieves relevant passages, then passes them to the LLM as context.',
    badges: ['Flowise RAG', 'Semantic Search', 'Context Window'],
  },
  {
    icon: Zap,         color: 'text-film-gold',   bg: 'bg-film-gold/10',
    title: 'Groq LLM Inference',
    desc:  'Powered by Groq\'s custom ASIC hardware, LLaMA 3 runs at 500+ tokens/second — giving near-instant, human-quality responses.',
    badges: ['LLaMA 3', '500 tok/s', 'Groq Cloud'],
  },
  {
    icon: MessageCircle, color: 'text-green-400', bg: 'bg-green-500/10',
    title: 'Conversational Memory',
    desc:  'FilmInsight maintains context across your full session, so follow-up questions flow naturally without repeating yourself.',
    badges: ['Session Memory', 'Context Aware', 'Multi-turn'],
  },
  {
    icon: Search,      color: 'text-purple-400',  bg: 'bg-purple-500/10',
    title: 'Semantic Vector Search',
    desc:  'Questions are embedded into the same vector space as screenplay chunks, enabling conceptually accurate retrieval — not just keyword matching.',
    badges: ['Dense Embeddings', 'Cosine Similarity', 'Top-K Retrieval'],
  },
  {
    icon: Quote,       color: 'text-pink-400',    bg: 'bg-pink-500/10',
    title: 'Famous Quotes Extraction',
    desc:  'Ask for memorable lines from any character, scene, or moment. FilmInsight finds the exact quote with scene context.',
    badges: ['Character Quotes', 'Scene Context', 'Screenplay Grounded'],
  },
  {
    icon: Users,       color: 'text-cyan-400',    bg: 'bg-cyan-500/10',
    title: 'Character Analysis',
    desc:  'Explore character arcs, relationships, motivations, and development throughout the screenplay with AI-powered insights.',
    badges: ['Character Arcs', 'Relationships', 'Motivations'],
  },
  {
    icon: Lightbulb,   color: 'text-amber-400',   bg: 'bg-amber-500/10',
    title: 'Themes & Symbolism',
    desc:  'Uncover hidden meanings, recurring motifs, and thematic elements embedded in the screenplay through deep analysis.',
    badges: ['Thematic Analysis', 'Symbolism', 'Motifs'],
  },
  {
    icon: Globe,       color: 'text-teal-400',    bg: 'bg-teal-500/10',
    title: 'Hybrid Knowledge',
    desc:  'Beyond the screenplay, FilmInsight enriches answers with movie trivia, IMDb ratings, cast info, and production facts.',
    badges: ['Trivia', 'IMDb Integration', 'Cast Info'],
  },
]

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
}
const itemVariants = {
  hidden:  { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
}

export default function Features() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="pt-24 pb-20 px-4"
    >
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-xs font-semibold uppercase tracking-widest text-film-red mb-3"
          >
            Capabilities
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="font-display font-black text-4xl sm:text-5xl text-white mb-4"
          >
            Everything FilmInsight <span className="gradient-text">Can Do</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-film-subtle max-w-2xl mx-auto"
          >
            A complete AI toolkit for exploring, understanding, and enjoying movie screenplays.
          </motion.p>
        </div>

        {/* Feature Cards */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-16"
        >
          {ALL_FEATURES.map(({ icon: Icon, color, bg, title, desc, badges }) => (
            <motion.div
              key={title}
              variants={itemVariants}
              whileHover={{ y: -5, scale: 1.01 }}
              className="glass border border-white/8 rounded-2xl p-6 hover:border-white/15 transition-all duration-300 group flex flex-col"
            >
              <div className={`w-12 h-12 rounded-2xl ${bg} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform flex-shrink-0`}>
                <Icon size={24} className={color} />
              </div>
              <h3 className="font-display font-bold text-white mb-2">{title}</h3>
              <p className="text-film-muted text-sm leading-relaxed flex-1 mb-4">{desc}</p>
              <div className="flex flex-wrap gap-1.5">
                {badges.map((b) => (
                  <span key={b} className="text-xs px-2 py-0.5 rounded-full glass border border-white/8 text-film-muted">
                    {b}
                  </span>
                ))}
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Comparison */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="glass border border-white/8 rounded-3xl p-8 mb-12"
        >
          <h2 className="font-display font-bold text-2xl text-white text-center mb-8">
            FilmInsight vs Traditional Search
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { label: 'Google Search', items: ['Generic results', 'No screenplay context', 'No conversation', 'Static information'], bad: true },
              { label: 'FilmInsight AI', items: ['Grounded in screenplay', 'Semantic understanding', 'Conversational memory', 'RAG + LLM synthesis'], bad: false },
            ].map(({ label, items, bad }) => (
              <div key={label} className={`rounded-2xl p-5 border ${bad ? 'bg-white/2 border-white/5' : 'bg-film-red/5 border-film-red/20'}`}>
                <h3 className={`font-semibold mb-4 ${bad ? 'text-film-muted' : 'text-film-red'}`}>{label}</h3>
                <ul className="space-y-2">
                  {items.map((item) => (
                    <li key={item} className="flex items-center gap-2 text-sm text-film-subtle">
                      <CheckCircle2 size={14} className={bad ? 'text-film-muted' : 'text-green-400'} />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </motion.div>

        {/* CTA */}
        <div className="text-center">
          <Link
            to="/chat"
            className="inline-flex items-center gap-2.5 px-8 py-3.5 bg-red-gradient rounded-xl font-semibold text-white glow-red hover:opacity-90 hover:scale-105 transition-all duration-300"
          >
            <MessageCircle size={18} />
            Try All Features
            <ChevronRight size={16} />
          </Link>
        </div>
      </div>
    </motion.div>
  )
}
