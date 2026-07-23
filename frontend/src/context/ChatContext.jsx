import { createContext, useContext, useReducer, useCallback } from 'react'

const ChatContext = createContext(null)

const initialState = {
  messages: [],
  isLoading: false,
  sessionId: crypto.randomUUID(),
  movieContext: null,
  movieTitle: null,   // plain string — set from the ?movie= URL param
  error: null,
}

function chatReducer(state, action) {
  switch (action.type) {
    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] }
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload }
    case 'SET_ERROR':
      return { ...state, error: action.payload }
    case 'SET_MOVIE_CONTEXT':
      return { ...state, movieContext: action.payload }
    case 'SET_MOVIE_TITLE':
      return { ...state, movieTitle: action.payload }
    case 'CLEAR_CHAT':
      return { ...initialState, sessionId: crypto.randomUUID() }
    case 'UPDATE_LAST_MESSAGE':
      return {
        ...state,
        messages: state.messages.map((m, i) =>
          i === state.messages.length - 1 ? { ...m, ...action.payload } : m
        ),
      }
    default:
      return state
  }
}

export function ChatProvider({ children }) {
  const [state, dispatch] = useReducer(chatReducer, initialState)

  const addMessage = useCallback((message) => {
    dispatch({ type: 'ADD_MESSAGE', payload: { ...message, id: crypto.randomUUID(), timestamp: new Date() } })
  }, [])

  const setLoading = useCallback((val) => dispatch({ type: 'SET_LOADING', payload: val }), [])
  const setError   = useCallback((err) => dispatch({ type: 'SET_ERROR',   payload: err }), [])
  const setMovieContext = useCallback((ctx) => dispatch({ type: 'SET_MOVIE_CONTEXT', payload: ctx }), [])
  const setMovieTitle   = useCallback((title) => dispatch({ type: 'SET_MOVIE_TITLE', payload: title }), [])
  const clearChat  = useCallback(() => dispatch({ type: 'CLEAR_CHAT' }), [])

  return (
    <ChatContext.Provider value={{ ...state, addMessage, setLoading, setError, setMovieContext, setMovieTitle, clearChat }}>
      {children}
    </ChatContext.Provider>
  )
}

export function useChat() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChat must be used within ChatProvider')
  return ctx
}
