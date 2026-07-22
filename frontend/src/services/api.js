import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request Interceptor ──────────────────────────────────────
api.interceptors.request.use(
  (config) => config,
  (error)  => Promise.reject(error)
)

// ── Response Interceptor ─────────────────────────────────────
api.interceptors.response.use(
  (response) => response.data,
  (error)    => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'
    return Promise.reject(new Error(message))
  }
)

// ── Chat API ─────────────────────────────────────────────────
export const chatAPI = {
  /**
   * Send a message to the FilmInsight RAG chatbot.
   * @param {string} question
   * @param {string} sessionId
   * @param {string} movieName
   * @returns {Promise<{ answer: string, sources: Array, metadata: object }>}
   */
  sendMessage: (question, sessionId, movieName) =>
    api.post('/chat', { question, sessionId, movie_name: movieName }),

  /**
   * Get chat history for the user.
   * @param {string} query Search term
   */
  getHistory: (query = '') =>
    api.get(`/chat/history`, { params: { query } }),

  /**
   * Delete a specific chat history record.
   */
  clearHistory: (chatId) =>
    api.delete(`/chat/history/${chatId}`),
}

// ── Movie API ─────────────────────────────────────────────────
export const movieAPI = {
  /**
   * Get movie details from TMDB / OMDB via backend.
   * @param {string} title
   */
  getMovieDetails: (title) =>
    api.get(`/movie/details`, { params: { title } }),

  /**
   * Get popular movies from TMDB with real posters.
   */
  getPopularMovies: (page = 1) =>
    api.get(`/movie/popular`, { params: { page } }),

  /**
   * Get our PDF script movies with real TMDB posters & ratings.
   */
  getOurMovies: () =>
    api.get(`/movie/our-movies`),

  /**
   * Upload a screenplay PDF to the document store.
   * @param {File} file
   * @param {function} onProgress
   */
  uploadScreenplay: (file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/movie/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        const pct = Math.round((e.loaded / e.total) * 100)
        onProgress?.(pct)
      },
    })
  },

  /**
   * List all uploaded screenplays.
   */
  listScreenplays: () =>
    api.get('/movie/screenplays'),
}

// ── Health API ────────────────────────────────────────────────
export const healthAPI = {
  check: () => api.get('/health'),
}

// ── Favorites API ─────────────────────────────────────────────
export const favoritesAPI = {
  getFavorites: () => api.get('/favorites'),
  addFavorite: (data) => api.post('/favorites', data),
  removeFavorite: (movieTitle) => api.delete(`/favorites/${encodeURIComponent(movieTitle)}`),
}

// ── Recent API ────────────────────────────────────────────────
export const recentAPI = {
  getRecent: () => api.get('/recent'),
  addRecent: (data) => api.post('/recent', data),
}

// ── User API ──────────────────────────────────────────────────
export const userAPI = {
  updateProfile: (data) => api.put('/api/auth/profile', data),
}

export default api
