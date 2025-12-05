import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark'

interface ThemeState {
  theme: Theme
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'dark',
      setTheme: (theme) => {
        set({ theme })
        updateDocumentTheme(theme)
      },
      toggleTheme: () => {
        const newTheme = get().theme === 'light' ? 'dark' : 'light'
        set({ theme: newTheme })
        updateDocumentTheme(newTheme)
      },
    }),
    {
      name: 'kalag-theme',
      onRehydrateStorage: () => (state) => {
        if (state) {
          updateDocumentTheme(state.theme)
        }
      },
    }
  )
)

function updateDocumentTheme(theme: Theme) {
  const root = document.documentElement
  if (theme === 'dark') {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}

// Initialize theme on load
if (typeof window !== 'undefined') {
  const stored = localStorage.getItem('kalag-theme')
  if (stored) {
    try {
      const { state } = JSON.parse(stored)
      updateDocumentTheme(state.theme)
    } catch {
      // Default to dark
      updateDocumentTheme('dark')
    }
  } else {
    // No stored preference, default to dark
    updateDocumentTheme('dark')
  }
}
