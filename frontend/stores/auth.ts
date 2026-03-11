import { create } from 'zustand'
import { authApi } from '@/lib/api-client'

interface AuthState {
  token: string | null
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<boolean>
  signup: (email: string, password: string, name?: string) => Promise<boolean>
  logout: () => void
  checkAuth: () => boolean
}

export const useAuth = create<AuthState>((set) => ({
  token: null,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await authApi.login({ email, password })
      const token = data.data.access_token
      localStorage.setItem('token', token)
      set({ token, isLoading: false })
      return true
    } catch (e: any) {
      set({ error: e.response?.data?.detail || 'Login failed', isLoading: false })
      return false
    }
  },

  signup: async (email, password, name) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await authApi.signup({ email, password, name })
      const token = data.data.access_token
      localStorage.setItem('token', token)
      set({ token, isLoading: false })
      return true
    } catch (e: any) {
      set({ error: e.response?.data?.detail || 'Signup failed', isLoading: false })
      return false
    }
  },

  logout: () => {
    localStorage.removeItem('token')
    set({ token: null })
    window.location.href = '/login'
  },

  checkAuth: () => {
    if (typeof window === 'undefined') return false
    const token = localStorage.getItem('token')
    if (token) set({ token })
    return !!token
  },
}))
