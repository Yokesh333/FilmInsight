export default function LoadingAnimation() {
  return (
    <div className="flex items-start gap-3 px-4 py-3">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-red-gradient flex items-center justify-center">
        <span className="text-xs font-bold text-white">AI</span>
      </div>

      {/* Bubble */}
      <div className="ai-bubble px-4 py-3 max-w-[200px]">
        <div className="flex items-center gap-1.5">
          <div className="typing-dot" />
          <div className="typing-dot" />
          <div className="typing-dot" />
          <span className="ml-1 text-xs text-film-muted">Thinking…</span>
        </div>
      </div>
    </div>
  )
}
