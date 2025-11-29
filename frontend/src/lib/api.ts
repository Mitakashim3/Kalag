/**
 * Kalag API Client
 * Axios instance with authentication interceptors
 */

import axios, { AxiosError } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Important: Send cookies with requests (for refresh token)
  withCredentials: true,
})

// Store the current access token
let currentToken: string | null = null

// Set auth token for requests
export function setAuthToken(token: string) {
  currentToken = token
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

// Clear auth token
export function clearAuthToken() {
  currentToken = null
  delete api.defaults.headers.common['Authorization']
}

// Request interceptor - add token to requests
api.interceptors.request.use(
  (config) => {
    if (currentToken && !config.headers['Authorization']) {
      config.headers['Authorization'] = `Bearer ${currentToken}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle 401 errors
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config
    
    // Don't retry refresh endpoint or if we already retried
    const isRefreshRequest = originalRequest?.url?.includes('/auth/refresh')
    const isLoginRequest = originalRequest?.url?.includes('/auth/login')
    const alreadyRetried = (originalRequest as any)?._retry
    
    // If 401 and it's not a refresh/login request and we haven't retried
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !isRefreshRequest &&
      !isLoginRequest &&
      !alreadyRetried
    ) {
      (originalRequest as any)._retry = true
      
      try {
        // Try to refresh the token
        const response = await api.post('/api/auth/refresh')
        const { access_token } = response.data
        
        setAuthToken(access_token)
        
        // Retry original request with new token
        originalRequest.headers['Authorization'] = `Bearer ${access_token}`
        return api(originalRequest)
      } catch {
        // Refresh failed - clear auth (don't redirect, let the app handle it)
        clearAuthToken()
        return Promise.reject(error)
      }
    }
    
    return Promise.reject(error)
  }
)

export default api
