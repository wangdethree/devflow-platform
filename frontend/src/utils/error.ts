import axios from 'axios'
import type { ApiErrorBody } from '@/types/api'

export function getErrorMessage(error: unknown, fallback = '请求失败，请稍后重试') {
  if (!axios.isAxiosError<ApiErrorBody>(error)) {
    return error instanceof Error ? error.message : fallback
  }

  const data = error.response?.data
  if (data?.message) return data.message
  if (typeof data?.detail === 'string') return data.detail
  if (Array.isArray(data?.detail)) {
    return data.detail.map((item) => item.msg).filter(Boolean).join('；') || fallback
  }
  return error.message || fallback
}
