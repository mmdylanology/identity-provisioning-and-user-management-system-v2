import React, { createContext, useState, useContext, useEffect } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setLoading(false)
      return
    }

    try {
      const response = await axios.get('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setUser(response.data)
    } catch (error) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    } finally {
      setLoading(false)
    }
  }

  const login = async (username, password) => {
    const response = await axios.post('/api/v1/auth/login', {
      username,
      password
    })

    const { access_token, refresh_token, user: userData } = response.data

    console.log('Access Token:', access_token)
    console.log('User Data:', userData)

    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    
    // If user data is provided, set it
    if (userData) {
      setUser(userData)
    } else {
      // Otherwise fetch user info from /auth/me
      const meResponse = await axios.get('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` }
      })
      setUser(meResponse.data)
    }

    return userData || user
  }

  const isSuperAdmin = () => {
    if (!user || !user.realm_access || !user.realm_access.roles) {
      return false
    }
    return user.realm_access.roles.includes('realm-admin')
  }

  const logout = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (token) {
        await axios.post('/api/v1/auth/logout', {}, {
          headers: { Authorization: `Bearer ${token}` }
        })
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      setUser(null)
    }
  }

  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
    isSuperAdmin: isSuperAdmin()
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
