/**
 * useApi Hook
 * Custom hook for making authenticated API requests
 */

import { useState, useCallback } from 'react'
import { api } from '@/lib/api'
import { AxiosError } from 'axios'

interface UseApiOptions {
  onSuccess?: (data: any) => void
  onError?: (error: string) => void
}

export function useApi<T = any>(options: UseApiOptions = {}) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const execute = useCallback(async (
    method: 'get' | 'post' | 'put' | 'delete',
    url: string,
    body?: any
  ) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await api[method](url, body)
      setData(response.data)
      options.onSuccess?.(response.data)
      return response.data
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      const errorMessage = axiosError.response?.data?.detail || 'An error occurred'
      setError(errorMessage)
      options.onError?.(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [options])

  const get = useCallback((url: string) => execute('get', url), [execute])
  const post = useCallback((url: string, body?: any) => execute('post', url, body), [execute])
  const put = useCallback((url: string, body?: any) => execute('put', url, body), [execute])
  const del = useCallback((url: string) => execute('delete', url), [execute])

  return {
    data,
    error,
    isLoading,
    get,
    post,
    put,
    delete: del,
    execute
  }
}
