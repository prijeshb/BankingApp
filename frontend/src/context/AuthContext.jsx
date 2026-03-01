import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { setAccessToken, setLogoutCallback } from '../api/client'
import * as authApi from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [accessToken, setToken] = useState(null)
  const [user, setUser]         = useState(null)
  const [loading, setLoading]   = useState(true)   // true while silent-login is pending

  // ── Clear all session state ───────────────────────────────────────────────
  const clearSession = useCallback(() => {
    setToken(null)
    setUser(null)
    setAccessToken(null)
    localStorage.removeItem('refresh_token')
  }, [])

  // Register the logout callback so the Axios interceptor can trigger it
  // when a refresh attempt fails (session truly expired).
  useEffect(() => {
    setLogoutCallback(clearSession)
  }, [clearSession])

  // ── Silent login on mount via stored refresh token ────────────────────────
  useEffect(() => {
    const storedRefresh = localStorage.getItem('refresh_token')
    if (!storedRefresh) { setLoading(false); return }

    authApi.refresh(storedRefresh)
      .then(async ({ data }) => {
        setAccessToken(data.access_token)
        setToken(data.access_token)
        const me = await authApi.getMe()
        setUser(me.data)
      })
      .catch(() => {
        localStorage.removeItem('refresh_token')
      })
      .finally(() => setLoading(false))
  }, [])   // eslint-disable-line react-hooks/exhaustive-deps

  // ── Actions ───────────────────────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    const { data } = await authApi.login(email, password)
    localStorage.setItem('refresh_token', data.refresh_token)
    setAccessToken(data.access_token)
    setToken(data.access_token)
    const me = await authApi.getMe()
    setUser(me.data)
    return me.data
  }, [])

  const logout = useCallback(async () => {
    const stored = localStorage.getItem('refresh_token')
    if (stored) {
      try { await authApi.logout(stored) } catch { /* token already invalid — ignore */ }
    }
    clearSession()
  }, [clearSession])

  const register = useCallback(async (email, password, full_name) => {
    const { data } = await authApi.register(email, password, full_name)
    return data
  }, [])

  return (
    <AuthContext.Provider value={{ accessToken, user, loading, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
