import axios from 'axios'

/**
 * Module-level token ref updated by AuthContext on every token change.
 * Using a ref (not React state) lets the Axios interceptors read the
 * latest token without being re-registered on every render.
 */
let _accessToken = null
let _onLogout = null

// Prevent concurrent refresh storms: queue up requests that fail while
// a refresh is already in flight.
let _isRefreshing = false
let _refreshQueue = []

export function setAccessToken(token) {
  _accessToken = token
}

export function setLogoutCallback(cb) {
  _onLogout = cb
}

const client = axios.create({ baseURL: '/api/v1' })

// ── Request interceptor: attach Bearer token ──────────────────────────────────
client.interceptors.request.use((config) => {
  if (_accessToken) {
    config.headers.Authorization = `Bearer ${_accessToken}`
  }
  return config
})

// ── Response interceptor: auto-refresh on 401 ────────────────────────────────
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config

    // Do not retry the refresh or login endpoints — that would infinite-loop.
    const isAuthEndpoint =
      original.url?.includes('/auth/refresh') ||
      original.url?.includes('/auth/login')

    if (
      error.response?.status !== 401 ||
      original._retry ||
      isAuthEndpoint
    ) {
      return Promise.reject(error)
    }

    original._retry = true

    // If a refresh is already in flight, queue this request.
    if (_isRefreshing) {
      return new Promise((resolve, reject) => {
        _refreshQueue.push({ resolve, reject })
      }).then((newToken) => {
        original.headers.Authorization = `Bearer ${newToken}`
        return client(original)
      })
    }

    _isRefreshing = true

    try {
      const stored = localStorage.getItem('refresh_token')
      if (!stored) throw new Error('No refresh token stored')

      const { data } = await axios.post('/api/v1/auth/refresh', {
        refresh_token: stored,
      })

      const newToken = data.access_token
      setAccessToken(newToken)

      // Drain the queue with the new token.
      _refreshQueue.forEach(({ resolve }) => resolve(newToken))
      _refreshQueue = []

      original.headers.Authorization = `Bearer ${newToken}`
      return client(original)
    } catch (refreshError) {
      _refreshQueue.forEach(({ reject }) => reject(refreshError))
      _refreshQueue = []
      _onLogout?.()
      return Promise.reject(refreshError)
    } finally {
      _isRefreshing = false
    }
  }
)

export default client
