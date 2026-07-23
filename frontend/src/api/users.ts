import { apiClient } from './client'
import type { PageResponse, User } from '@/types/api'

export const usersApi = {
  me: () => apiClient.get<User>('/users/me'),
  permissions: () => apiClient.get<{ permissions: string[] }>('/users/me/permissions'),
  updateMe: (payload: Partial<Pick<User, 'username' | 'email' | 'avatar'>>) =>
    apiClient.patch<User>('/users/me', payload),
  list: (params: { page: number; page_size: number }) =>
    apiClient.get<PageResponse<User>>('/admin/users', { params }),
  updateStatus: (id: number, isActive: boolean) =>
    apiClient.patch<User>(`/admin/users/${id}/status`, { is_active: isActive }),
}
