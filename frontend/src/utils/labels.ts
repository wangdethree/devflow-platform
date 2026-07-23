import type { IssuePriority, IssueStatus, IssueType, ProjectRole, ProjectStatus, ReviewStatus } from '@/types/api'

export const projectStatusLabels: Record<ProjectStatus, string> = {
  ACTIVE: '进行中',
  ARCHIVED: '已归档',
}

export const roleLabels: Record<ProjectRole, string> = {
  Owner: '负责人',
  Developer: '开发者',
  Viewer: '访客',
}

export const issueTypeLabels: Record<IssueType, string> = {
  BUG: '缺陷',
  FEATURE: '需求',
  TASK: '任务',
}

export const priorityLabels: Record<IssuePriority, string> = {
  LOW: '低',
  MEDIUM: '中',
  HIGH: '高',
  CRITICAL: '紧急',
}

export const issueStatusLabels: Record<IssueStatus, string> = {
  OPEN: '待处理',
  IN_PROGRESS: '处理中',
  REVIEW: '待评审',
  DONE: '已完成',
}

export const reviewStatusLabels: Record<ReviewStatus, string> = {
  PENDING: '待处理',
  APPROVED: '已通过',
  REJECTED: '已驳回',
}

export function tagType(value: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' {
  if (['ACTIVE', 'IN_PROGRESS', 'FEATURE', 'APPROVED', 'Developer'].includes(value)) return 'primary'
  if (['DONE'].includes(value)) return 'success'
  if (['REVIEW', 'PENDING', 'HIGH'].includes(value)) return 'warning'
  if (['CRITICAL', 'REJECTED', 'BUG'].includes(value)) return 'danger'
  return 'info'
}
