import { apiClient } from './client'
import type {
  Comment,
  Issue,
  IssueForm,
  IssuePriority,
  IssueStatus,
  IssueType,
  ListResponse,
  PageResponse,
  Review,
  ReviewStatus,
} from '@/types/api'

export interface IssueFilters {
  project_id?: number
  creator_id?: number
  assignee_id?: number
  status?: IssueStatus
  type?: IssueType
  priority?: IssuePriority
  keyword?: string
  page: number
  page_size: number
}

export const issuesApi = {
  list: (params: IssueFilters) => apiClient.get<PageResponse<Issue>>('/issues', { params }),
  get: (id: number) => apiClient.get<Issue>(`/issues/${id}`),
  create: (projectId: number, payload: IssueForm) =>
    apiClient.post<Issue>(`/projects/${projectId}/issues`, payload),
  update: (id: number, payload: Partial<IssueForm> & { version: number }) =>
    apiClient.patch<Issue>(`/issues/${id}`, payload),
  updateStatus: (id: number, status: IssueStatus, version: number) =>
    apiClient.patch<Issue>(`/issues/${id}/status`, { status, version }),
  remove: (id: number, version: number) => apiClient.delete(`/issues/${id}`, { params: { version } }),
  comments: (id: number) => apiClient.get<ListResponse<Comment>>(`/issues/${id}/comments`),
  createComment: (id: number, content: string) =>
    apiClient.post<Comment>(`/issues/${id}/comments`, { content }),
  updateComment: (issueId: number, commentId: number, content: string) =>
    apiClient.patch<Comment>(`/issues/${issueId}/comments/${commentId}`, { content }),
  removeComment: (issueId: number, commentId: number) =>
    apiClient.delete(`/issues/${issueId}/comments/${commentId}`),
  reviews: (id: number) => apiClient.get<ListResponse<Review>>(`/issues/${id}/reviews`),
  createReview: (id: number, reviewerId: number, issueVersion: number) =>
    apiClient.post<Review>(`/issues/${id}/reviews`, {
      reviewer_id: reviewerId,
      issue_version: issueVersion,
    }),
  decideReview: (reviewId: number, status: ReviewStatus, comment?: string) =>
    apiClient.patch<Review>(`/reviews/${reviewId}`, { status, comment: comment || null }),
}
