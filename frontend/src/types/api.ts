export type ProjectStatus = 'ACTIVE' | 'ARCHIVED'
export type ProjectRole = 'Owner' | 'Developer' | 'Viewer'
export type IssueType = 'BUG' | 'FEATURE' | 'TASK'
export type IssuePriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type IssueStatus = 'OPEN' | 'IN_PROGRESS' | 'REVIEW' | 'DONE'
export type ReviewStatus = 'PENDING' | 'APPROVED' | 'REJECTED'

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  refresh_expires_in: number
}

export interface User {
  id: number
  username: string
  email: string
  avatar: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Project {
  id: number
  name: string
  description: string | null
  status: ProjectStatus
  owner_id: number
  created_at: string
  updated_at: string
}

export interface ProjectMember {
  id: number
  project_id: number
  user_id: number
  username: string
  email: string
  role: ProjectRole
  joined_at: string
}

export interface Issue {
  id: number
  project_id: number
  creator_id: number
  assignee_id: number | null
  title: string
  description: string | null
  type: IssueType
  priority: IssuePriority
  status: IssueStatus
  version: number
  created_at: string
  updated_at: string
}

export interface Comment {
  id: number
  issue_id: number
  user_id: number
  content: string
  created_at: string
}

export interface Review {
  id: number
  issue_id: number
  requester_id: number
  reviewer_id: number
  status: ReviewStatus
  comment: string | null
  created_at: string
}

export interface Notification {
  id: number
  type: string
  target_type: string
  target_id: number
  content: string
  is_read: boolean
  created_at: string
}

export interface PageResponse<T> {
  items: T[]
  page: number
  page_size: number
  total: number
}

export interface ListResponse<T> {
  items: T[]
}

export interface ProjectForm {
  name: string
  description?: string | null
  status: ProjectStatus
}

export interface IssueForm {
  title: string
  description?: string | null
  type: IssueType
  priority: IssuePriority
  assignee_id?: number | null
}

export interface ApiErrorBody {
  message?: string
  detail?: string | Array<{ msg?: string }>
  code?: string
  request_id?: string
}
