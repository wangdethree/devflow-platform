import { apiClient } from './client'
import type { ListResponse, PageResponse, Project, ProjectForm, ProjectMember, ProjectRole } from '@/types/api'

export const projectsApi = {
  list: (params: { page: number; page_size: number }) =>
    apiClient.get<PageResponse<Project>>('/projects', { params }),
  get: (id: number) => apiClient.get<Project>(`/projects/${id}`),
  create: (payload: ProjectForm) => apiClient.post<Project>('/projects', payload),
  update: (id: number, payload: Partial<ProjectForm>) =>
    apiClient.patch<Project>(`/projects/${id}`, payload),
  remove: (id: number) => apiClient.delete(`/projects/${id}`),
  members: (id: number) => apiClient.get<ListResponse<ProjectMember>>(`/projects/${id}/members`),
  addMember: (id: number, payload: { user_id: number; role: ProjectRole }) =>
    apiClient.post<ProjectMember>(`/projects/${id}/members`, payload),
  updateMember: (projectId: number, userId: number, role: ProjectRole) =>
    apiClient.patch<ProjectMember>(`/projects/${projectId}/members/${userId}`, { role }),
  removeMember: (projectId: number, userId: number) =>
    apiClient.delete(`/projects/${projectId}/members/${userId}`),
}
