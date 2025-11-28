import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'
import { useAuthStore } from './store/authStore'

// Initialize auth ONCE when app starts (silent token refresh)
useAuthStore.getState().initializeAuth()

// Initialize theme from localStorage
const initializeTheme = () => {
  const stored = localStorage.getItem('kalag-theme')
  if (stored) {
    try {
      const { state } = JSON.parse(stored)
      if (state?.theme === 'dark') {
        document.documentElement.classList.add('dark')
      }
    } catch {
      // Default to light
    }
  }
}
initializeTheme()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
