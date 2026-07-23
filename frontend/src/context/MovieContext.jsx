import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { movieAPI } from '../services/api'

const MovieContext = createContext(null)

export function MovieProvider({ children }) {
  const [movies, setMovies] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refreshMovies = useCallback(async () => {
    try {
      const data = await movieAPI.getOurMovies()
      setMovies(data.movies || [])
      setError(null)
    } catch (err) {
      console.error("Failed to fetch movies in registry:", err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshMovies()
  }, [refreshMovies])

  // Periodic polling for status changes (e.g. PROCESSING -> READY)
  useEffect(() => {
    const interval = setInterval(() => {
      const hasPending = movies.some(m => m.status === 'UPLOADED' || m.status === 'PROCESSING')
      if (hasPending) {
        movieAPI.getOurMovies().then(data => {
          setMovies(data.movies || [])
        }).catch(err => console.error("Polling movies failed:", err))
      }
    }, 4000)

    return () => clearInterval(interval)
  }, [movies])

  return (
    <MovieContext.Provider value={{ movies, loading, error, refreshMovies }}>
      {children}
    </MovieContext.Provider>
  )
}

export function useMovies() {
  const ctx = useContext(MovieContext)
  if (!ctx) throw new Error('useMovies must be used within a MovieProvider')
  return ctx
}
