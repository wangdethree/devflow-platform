import { apiClient } from './client'
import type { TokenResponse, User } from '@/types/api'

export const authApi = {
  register: (payload: { username: string; email: string; password: string }) =>
    apiClient.post<User>('/auth/register', payload),
  login: (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password })
    return apiClient.post<TokenResponse>('/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },
  refresh: (refreshToken: string) =>
    apiClient.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken }),
  logout: () => apiClient.post<{ revoked_sessions: number }>('/auth/logout'),
  logoutAll: () => apiClient.post<{ revoked_sessions: number }>('/auth/logout-all'),
}
