import { apiClient } from './client'
import type { Notification, PageResponse } from '@/types/api'

export const notificationsApi = {
  list: (params: { page: number; page_size: number; is_read?: boolean }) =>
    apiClient.get<PageResponse<Notification>>('/notifications', { params }),
  unreadCount: () => apiClient.get<{ unread_count: number }>('/notifications/unread-count'),
  markRead: (id: number) => apiClient.patch<Notification>(`/notifications/${id}/read`),
  markAllRead: () => apiClient.patch<{ updated_count: number }>('/notifications/read-all'),
}
