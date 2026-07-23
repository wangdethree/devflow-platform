import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiErrorBody, TokenResponse } from '@/types/api'
import { clearTokens, getAccessToken, getRefreshToken, saveTokens } from '@/utils/storage'
import { getErrorMessage } from '@/utils/error'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

export const apiClient = axios.create({
  baseURL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

const refreshClient = axios.create({ baseURL, timeout: 15000 })
// Refresh Token 会轮换；共享 Promise 可避免多个 401 同时消费同一个一次性令牌。
let refreshPromise: Promise<string> | null = null

interface RetryRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

function redirectToLogin() {
  clearTokens()
  if (window.location.pathname === '/login') return
  const redirect = encodeURIComponent(`${window.location.pathname}${window.location.search}`)
  window.location.assign(`/login?redirect=${redirect}`)
}

async function refreshAccessToken() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) throw new Error('登录状态已失效')
  const { data } = await refreshClient.post<TokenResponse>('/auth/refresh', {
    refresh_token: refreshToken,
  })
  saveTokens(data)
  return data.access_token
}

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const originalRequest = error.config as RetryRequestConfig | undefined
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      // 每个失败请求最多重放一次，防止刷新失败时形成无限递归。
      originalRequest._retry = true
      refreshPromise ??= refreshAccessToken().finally(() => {
        refreshPromise = null
      })

      try {
        const token = await refreshPromise
        originalRequest.headers.Authorization = `Bearer ${token}`
        return await apiClient(originalRequest)
      } catch {
        redirectToLogin()
      }
    }

    if (error.response?.status === 403) {
      ElMessage.error(getErrorMessage(error, '你没有执行此操作的权限'))
    }
    return Promise.reject(error)
  },
)
