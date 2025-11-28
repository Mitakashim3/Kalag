/**
 * Kalag Auth Store
 * Zustand store for authentication state management
 * 
 * Security Design:
 * - Access token stored in memory (not localStorage) - XSS protected
 * - Refresh token stored in HttpOnly cookie by backend - cannot be accessed by JS
 * - Silent refresh happens before token expiry
 */

import { create } from 'zustand'
import { api, setAuthToken, clearAuthToken } from '@/lib/api'

interface User {
  id: string
  email: string
  full_name: string | null
  is_active: boolean
  created_at: string
}

interface AuthState {
  user: User | null
  accessToken: string | null
  expiresAt: number | null
  isAuthenticated: boolean
  isLoading: boolean
  
  // Actions
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<boolean>
  initializeAuth: () => Promise<void>
  setUser: (user: User | null) => void
}

// Calculate when to refresh (30 seconds before expiry)
const REFRESH_BUFFER_MS = 30 * 1000

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  expiresAt: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (email: string, password: string) => {
    const response = await api.post('/api/auth/login', { email, password })
    const { access_token, expires_in } = response.data
    
    const expiresAt = Date.now() + (expires_in * 1000)
    
    // Set token in memory and axios instance
    set({ accessToken: access_token, expiresAt, isAuthenticated: true })
    setAuthToken(access_token)
    
    // Fetch user profile
    const userResponse = await api.get('/api/auth/me')
    set({ user: userResponse.data })
    
    // Schedule token refresh
    scheduleTokenRefresh(expiresAt, get().refreshToken)
  },

  register: async (email: string, password: string, fullName?: string) => {
    await api.post('/api/auth/register', {
      email,
      password,
      full_name: fullName
    })
  },

  logout: async () => {
    try {
      await api.post('/api/auth/logout')
    } catch {
      // Ignore errors - we're logging out anyway
    }
    
    // Clear state
    set({
      user: null,
      accessToken: null,
      expiresAt: null,
      isAuthenticated: false
    })
    clearAuthToken()
    
    // Clear any scheduled refresh
    if (refreshTimeoutId) {
      clearTimeout(refreshTimeoutId)
      refreshTimeoutId = null
    }
  },

  refreshToken: async () => {
    try {
      // Call refresh endpoint - browser sends HttpOnly cookie automatically
      const response = await api.post('/api/auth/refresh')
      const { access_token, expires_in } = response.data
      
      const expiresAt = Date.now() + (expires_in * 1000)
      
      // Update state with new token
      set({ accessToken: access_token, expiresAt, isAuthenticated: true })
      setAuthToken(access_token)
      
      // Schedule next refresh
      scheduleTokenRefresh(expiresAt, get().refreshToken)
      
      return true
    } catch (error: any) {
      // Only log non-401 errors (401 is expected when not logged in)
      if (error?.response?.status !== 401) {
        console.error('Token refresh failed:', error)
      }
      
      // Refresh failed - user needs to login again
      set({
        user: null,
        accessToken: null,
        expiresAt: null,
        isAuthenticated: false,
        isLoading: false
      })
      clearAuthToken()
      return false
    }
  },

  initializeAuth: async () => {
    // Prevent multiple simultaneous initializations
    if (isInitializing) {
      return
    }
    
    isInitializing = true
    set({ isLoading: true })
    
    try {
      // Try to refresh token using the HttpOnly cookie
      const success = await get().refreshToken()
      
      if (success) {
        // Fetch user profile
        const userResponse = await api.get('/api/auth/me')
        set({ user: userResponse.data, isLoading: false })
      } else {
        set({ isLoading: false })
      }
    } catch {
      set({ isLoading: false })
    } finally {
      isInitializing = false
    }
  },

  setUser: (user: User | null) => set({ user })
}))

// Token refresh scheduling
let refreshTimeoutId: ReturnType<typeof setTimeout> | null = null
let isInitializing = false

function scheduleTokenRefresh(expiresAt: number, refreshFn: () => Promise<boolean>) {
  // Clear any existing timeout
  if (refreshTimeoutId) {
    clearTimeout(refreshTimeoutId)
  }
  
  // Calculate when to refresh (30 seconds before expiry)
  const refreshAt = expiresAt - REFRESH_BUFFER_MS
  const delay = refreshAt - Date.now()
  
  if (delay > 0) {
    refreshTimeoutId = setTimeout(async () => {
      await refreshFn()
    }, delay)
  }
}
