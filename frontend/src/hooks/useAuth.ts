/**
 * useAuth Hook
 * Provides authentication state and actions to components
 */

import { useAuthStore } from '@/store/authStore'

export function useAuth() {
  const {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout
  } = useAuthStore()

  // NOTE: Initialization is now handled in main.tsx, not here
  // This prevents multiple components from triggering init

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout
  }
}
