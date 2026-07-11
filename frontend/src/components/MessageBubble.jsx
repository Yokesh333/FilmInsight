import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Copy, Check, ThumbsUp, ThumbsDown, User, ChevronDown, ChevronUp, FileText, Hash } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

function formatTime(date) {
  return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

/* ── Markdown Components ────────────────────────────────────────── */
const mdComponents = {
  code({ node, inline, className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || '')
    return !inline && match ? (
      <SyntaxHighlighter
        style={oneDark}
        language={match[1]}
        PreTag="div"
        customStyle={{ borderRadius: '10px', fontSize: '13px', margin: '8px 0', border: '1px solid rgba(255,255,255,0.08)' }}
        {...props}
      >
        {String(children).replace(/\n$/, '')}
      </SyntaxHighlighter>
    ) : (
      <code className="px-1.5 py-0.5 rounded-md bg-white/8 font-mono text-[13px] text-pink-300" {...props}>
        {children}
      </code>
    )
  },
  h1: ({ children }) => <h1 className="text-xl font-display font-bold text-white mt-4 mb-2 pb-1 border-b border-white/10">{children}</h1>,
  h2: ({ children }) => <h2 className="text-lg font-display font-bold text-white mt-4 mb-2">{children}</h2>,
  h3: ({ children }) => <h3 className="text-base font-semibold text-white/90 mt-3 mb-1.5">{children}</h3>,
  p:  ({ children }) => <p className="leading-7 text-[15px] text-film-subtle mb-3 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="space-y-1.5 my-2 pl-1">{children}</ul>,
  ol: ({ children }) => <ol className="space-y-1.5 my-2 pl-4 list-decimal">{children}</ol>,
  li: ({ children }) => (
    <li className="flex items-start gap-2 text-[14px] text-film-subtle">
      <span className="mt-2 w-1.5 h-1.5 rounded-full bg-film-red flex-shrink-0" />
      <span>{children}</span>
    </li>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-film-red pl-4 my-3 italic text-film-subtle/80">{children}</blockquote>
  ),
  strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
  em: ({ children }) => <em className="italic text-film-subtle/90">{children}</em>,
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-film-red hover:underline">{children}</a>
  ),
  table: ({ children }) => (
    <div className="overflow-x-auto my-3">
      <table className="w-full text-sm border-collapse">{children}</table>
    </div>
  ),
  th: ({ children }) => <th className="border border-white/10 px-3 py-2 text-left font-semibold text-white bg-white/5">{children}</th>,
  td: ({ children }) => <td className="border border-white/10 px-3 py-2 text-film-subtle">{children}</td>,
  hr: () => <hr className="border-white/10 my-4" />,
}

/* ── Source Section ─────────────────────────────────────────────── */
function SourcesSection({ sources }) {
  const [open, setOpen] = useState(false)
  if (!sources?.length) return null
  return (
    <div className="mt-3 border-t border-white/5 pt-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-xs text-film-muted hover:text-film-subtle transition-colors"
      >
        <FileText size={12} />
        {sources.length} source{sources.length > 1 ? 's' : ''} retrieved
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden mt-2 space-y-1.5"
          >
            {sources.map((src, i) => (
              <div key={i} className="flex items-start gap-2 text-xs glass border border-white/8 rounded-lg px-2.5 py-2">
                <Hash size={10} className="text-film-red flex-shrink-0 mt-0.5" />
                <div className="min-w-0">
                  <p className="text-film-subtle font-medium">{src.pageLabel || `Source ${i + 1}`}</p>
                  {src.content && <p className="text-film-muted line-clamp-2 mt-0.5">"{src.content}"</p>}
                </div>
                {src.score !== undefined && (
                  <span className="flex-shrink-0 px-1.5 py-0.5 rounded-full bg-green-500/15 text-green-400 text-xs">
                    {Math.round(src.score * 100)}%
                  </span>
                )}
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/* ── Main Component ─────────────────────────────────────────────── */
export default function MessageBubble({ message }) {
  const { role, content, timestamp, sources } = message
  const isUser = role === 'user'
  const [copied, setCopied] = useState(false)
  const [liked,  setLiked]  = useState(null)

  const handleCopy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={`flex gap-3 px-4 py-2 group ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold self-start mt-1 ${
        isUser ? 'bg-white/10 border border-white/15 text-white' : 'bg-red-gradient text-white'
      }`}>
        {isUser ? <User size={14} /> : '✦'}
      </div>

      {/* Content */}
      <div className={`flex flex-col ${isUser ? 'items-end max-w-[75%]' : 'items-start flex-1 min-w-0'}`}>
        {/* Bubble */}
        {isUser ? (
          <div className="user-bubble px-4 py-3 text-white text-[15px] leading-relaxed">
            {content}
          </div>
        ) : (
          <div className="w-full">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={mdComponents}
            >
              {content}
            </ReactMarkdown>

            {/* Sources */}
            <SourcesSection sources={sources} />
          </div>
        )}

        {/* Actions row */}
        <div className={`flex items-center gap-1.5 mt-1 px-1 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
          <span className="text-[11px] text-film-muted">{formatTime(timestamp)}</span>
          {!isUser && (
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={handleCopy}
                title="Copy response"
                className="p-1 rounded-md hover:bg-white/5 text-film-muted hover:text-white transition-colors"
              >
                {copied ? <Check size={12} className="text-green-400" /> : <Copy size={12} />}
              </button>
              <button
                onClick={() => setLiked(true)}
                className={`p-1 rounded-md hover:bg-white/5 transition-colors ${liked === true ? 'text-green-400' : 'text-film-muted hover:text-white'}`}
              >
                <ThumbsUp size={12} />
              </button>
              <button
                onClick={() => setLiked(false)}
                className={`p-1 rounded-md hover:bg-white/5 transition-colors ${liked === false ? 'text-film-red' : 'text-film-muted hover:text-white'}`}
              >
                <ThumbsDown size={12} />
              </button>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
