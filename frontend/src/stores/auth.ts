import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'
import { usersApi } from '@/api/users'
import type { User } from '@/types/api'
import { clearTokens, getAccessToken, saveTokens } from '@/utils/storage'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(getAccessToken())
  const user = ref<User | null>(null)
  const permissions = ref<string[]>([])
  const initialized = ref(false)

  const isAuthenticated = computed(() => Boolean(accessToken.value && user.value))
  const isAdmin = computed(
    () => permissions.value.includes('user:read') || permissions.value.includes('user:manage'),
  )

  async function loadSession() {
    if (!getAccessToken()) {
      initialized.value = true
      return
    }
    try {
      const [userResponse, permissionResponse] = await Promise.all([
        usersApi.me(),
        usersApi.permissions(),
      ])
      user.value = userResponse.data
      permissions.value = permissionResponse.data.permissions
    } catch {
      clearSession()
    } finally {
      initialized.value = true
    }
  }

  async function login(email: string, password: string) {
    const { data } = await authApi.login(email, password)
    saveTokens(data)
    accessToken.value = data.access_token
    initialized.value = false
    await loadSession()
  }

  async function register(payload: { username: string; email: string; password: string }) {
    return authApi.register(payload)
  }

  async function logout() {
    try {
      if (getAccessToken()) await authApi.logout()
    } finally {
      clearSession()
    }
  }

  function clearSession() {
    clearTokens()
    accessToken.value = null
    user.value = null
    permissions.value = []
    initialized.value = true
  }

  function updateUser(updated: User) {
    user.value = updated
  }

  return {
    accessToken,
    user,
    permissions,
    initialized,
    isAuthenticated,
    isAdmin,
    loadSession,
    login,
    register,
    logout,
    clearSession,
    updateUser,
  }
})
