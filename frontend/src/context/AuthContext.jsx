import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { getMe } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setLoading(false)
      return
    }
    getMe()
      .then(setUser)
      .catch(() => localStorage.clear())
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback((tokens, userData) => {
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    setUser(userData)
  }, [])

  const logout = useCallback(() => {
    localStorage.clear()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
