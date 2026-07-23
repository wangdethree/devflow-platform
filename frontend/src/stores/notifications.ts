import { ref } from 'vue'
import { defineStore } from 'pinia'
import { notificationsApi } from '@/api/notifications'

export const useNotificationStore = defineStore('notifications', () => {
  const unreadCount = ref(0)

  async function refreshUnreadCount() {
    const { data } = await notificationsApi.unreadCount()
    unreadCount.value = data.unread_count
  }

  function decrementUnread() {
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }

  function clearUnread() {
    unreadCount.value = 0
  }

  return { unreadCount, refreshUnreadCount, decrementUnread, clearUnread }
})
