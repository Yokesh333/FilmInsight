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
   * @returns {Promise<{ answer: string, sources: Array, metadata: object }>}
   */
  sendMessage: (question, sessionId) =>
    api.post('/chat', { question, sessionId }),

  /**
   * Get chat history for a session.
   * @param {string} sessionId
   */
  getHistory: (sessionId) =>
    api.get(`/chat/history/${sessionId}`),

  /**
   * Clear chat history for a session.
   */
  clearHistory: (sessionId) =>
    api.delete(`/chat/history/${sessionId}`),
}

// ── Movie API ─────────────────────────────────────────────────
export const movieAPI = {
  /**
   * Get movie details from OMDB / backend.
   * @param {string} title
   */
  getMovieDetails: (title) =>
    api.get(`/movie/details`, { params: { title } }),

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

export default api
