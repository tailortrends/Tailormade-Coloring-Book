import axios from 'axios'
import { useAuthStore } from '@/store/auth'

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000, // 2 min — AI generation takes time
})

// Attach Firebase token to every request automatically
apiClient.interceptors.request.use(async (config) => {
  const auth = useAuthStore()
  const token = await auth.getIdToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Friendly error messages
apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail

    if (status === 401) {
      const auth = useAuthStore()
      auth.signOut()
    }

    // Surface the backend's detail message if available
    const message = detail || error.message || 'Something went wrong. Please try again.'
    return Promise.reject(new Error(message))
  }
)
