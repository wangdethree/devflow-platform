# DevFlow 前端 API 映射

本文以当前后端路由、Pydantic Schema 和 2026-07-23 本地运行态 OpenAPI 为准。

状态说明：

- **真实联调通过**：曾对本地 FastAPI + MySQL + Redis 发起真实请求并检查响应或状态变化。
- **构建验证**：前端已实现并通过 TypeScript/生产构建，但本轮没有单独改变数据验证。
- **异常联调通过**：真实验证了预期的 401 或 403。

| 前端页面 | 前端 API 函数 | 方法 | 后端路径 | 请求类型 | 响应类型 | 后端路由文件 | 验证状态 |
|---|---|---:|---|---|---|---|---|
| 注册 | `authApi.register` | POST | `/api/v1/auth/register` | JSON `RegisterRequest` | `UserResponse` | `backend/app/api/v1/auth.py` | 真实联调通过 |
| 登录 | `authApi.login` | POST | `/api/v1/auth/login` | Form `OAuth2PasswordRequestForm` | `TokenResponse` | `backend/app/api/v1/auth.py` | 真实联调通过 |
| 登录恢复 | `usersApi.me` | GET | `/api/v1/users/me` | Bearer Token | `UserResponse` | `backend/app/api/v1/users.py` | 真实联调通过 |
| 权限恢复 | `usersApi.permissions` | GET | `/api/v1/users/me/permissions` | Bearer Token | `PermissionListResponse` | `backend/app/api/v1/users.py` | 真实联调通过 |
| Token 轮换 | 拦截器内部刷新 | POST | `/api/v1/auth/refresh` | JSON `RefreshTokenRequest` | `TokenResponse` | `backend/app/api/v1/auth.py` | 真实联调通过 |
| 退出 | `authApi.logout` | POST | `/api/v1/auth/logout` | Bearer Token | `LogoutResponse` | `backend/app/api/v1/auth.py` | 真实联调通过 |
| 全部退出 | `authApi.logoutAll` | POST | `/api/v1/auth/logout-all` | Bearer Token | `LogoutResponse` | `backend/app/api/v1/auth.py` | 构建验证 |
| 工作台/项目 | `projectsApi.list` | GET | `/api/v1/projects` | Query `page,page_size` | `ProjectListResponse` | `backend/app/api/v1/projects.py` | 真实联调通过 |
| 项目详情 | `projectsApi.get` | GET | `/api/v1/projects/{project_id}` | Path | `ProjectResponse` | `backend/app/api/v1/projects.py` | 真实联调通过 |
| 创建项目 | `projectsApi.create` | POST | `/api/v1/projects` | JSON `ProjectCreateRequest` | `ProjectResponse` | `backend/app/api/v1/projects.py` | 真实联调通过 |
| 编辑项目 | `projectsApi.update` | PATCH | `/api/v1/projects/{project_id}` | JSON `ProjectUpdateRequest` | `ProjectResponse` | `backend/app/api/v1/projects.py` | 构建验证 |
| 删除项目 | `projectsApi.remove` | DELETE | `/api/v1/projects/{project_id}` | Path | 204 | `backend/app/api/v1/projects.py` | 真实联调通过 |
| 项目成员 | `projectsApi.members` | GET | `/api/v1/projects/{project_id}/members` | Path | `ProjectMemberListResponse` | `backend/app/api/v1/projects.py` | 真实联调通过 |
| 添加成员 | `projectsApi.addMember` | POST | `/api/v1/projects/{project_id}/members` | JSON `ProjectMemberCreateRequest` | `ProjectMemberResponse` | `backend/app/api/v1/projects.py` | 真实联调通过 |
| 修改成员角色 | `projectsApi.updateMember` | PATCH | `/api/v1/projects/{project_id}/members/{user_id}` | JSON `ProjectMemberUpdateRequest` | `ProjectMemberResponse` | `backend/app/api/v1/projects.py` | 构建验证 |
| 移除成员 | `projectsApi.removeMember` | DELETE | `/api/v1/projects/{project_id}/members/{user_id}` | Path | 204 | `backend/app/api/v1/projects.py` | 构建验证 |
| Issue 列表 | `issuesApi.list` | GET | `/api/v1/issues` | Query 筛选 + 分页 | `IssueListResponse` | `backend/app/api/v1/issues.py` | 真实联调通过 |
| Issue 详情 | `issuesApi.get` | GET | `/api/v1/issues/{issue_id}` | Path | `IssueResponse` | `backend/app/api/v1/issues.py` | 真实联调通过 |
| 创建 Issue | `issuesApi.create` | POST | `/api/v1/projects/{project_id}/issues` | JSON `IssueCreateRequest` | `IssueResponse` | `backend/app/api/v1/issues.py` | 真实联调通过 |
| 编辑 Issue | `issuesApi.update` | PATCH | `/api/v1/issues/{issue_id}` | JSON `IssueUpdateRequest`（含 version） | `IssueResponse` | `backend/app/api/v1/issues.py` | 构建验证 |
| 状态流转 | `issuesApi.updateStatus` | PATCH | `/api/v1/issues/{issue_id}/status` | JSON `IssueStatusRequest` | `IssueResponse` | `backend/app/api/v1/issues.py` | 真实联调通过 |
| 软删除 Issue | `issuesApi.remove` | DELETE | `/api/v1/issues/{issue_id}?version=` | Query version | 204 | `backend/app/api/v1/issues.py` | 构建验证 |
| 评论列表 | `issuesApi.comments` | GET | `/api/v1/issues/{issue_id}/comments` | Path | `CommentListResponse` | `backend/app/api/v1/comments.py` | 真实联调通过 |
| 发表评论 | `issuesApi.createComment` | POST | `/api/v1/issues/{issue_id}/comments` | JSON `CommentCreateRequest` | `CommentResponse` | `backend/app/api/v1/comments.py` | 真实联调通过 |
| 编辑评论 | `issuesApi.updateComment` | PATCH | `/api/v1/issues/{issue_id}/comments/{comment_id}` | JSON `CommentUpdateRequest` | `CommentResponse` | `backend/app/api/v1/comments.py` | 构建验证 |
| 删除评论 | `issuesApi.removeComment` | DELETE | `/api/v1/issues/{issue_id}/comments/{comment_id}` | Path | 204 | `backend/app/api/v1/comments.py` | 构建验证 |
| Review 历史 | `issuesApi.reviews` | GET | `/api/v1/issues/{issue_id}/reviews` | Path | `ReviewListResponse` | `backend/app/api/v1/reviews.py` | 真实联调通过 |
| 发起 Review | `issuesApi.createReview` | POST | `/api/v1/issues/{issue_id}/reviews` | JSON `ReviewCreateRequest` | `ReviewResponse` | `backend/app/api/v1/reviews.py` | 真实联调通过 |
| 处理 Review | `issuesApi.decideReview` | PATCH | `/api/v1/reviews/{review_id}` | JSON `ReviewDecisionRequest` | `ReviewResponse` | `backend/app/api/v1/reviews.py` | 真实联调通过 |
| 通知列表 | `notificationsApi.list` | GET | `/api/v1/notifications` | Query 筛选 + 分页 | `NotificationListResponse` | `backend/app/api/v1/notifications.py` | 真实联调通过 |
| 未读数 | `notificationsApi.unreadCount` | GET | `/api/v1/notifications/unread-count` | Bearer Token | `UnreadCountResponse` | `backend/app/api/v1/notifications.py` | 真实联调通过 |
| 单条已读 | `notificationsApi.markRead` | PATCH | `/api/v1/notifications/{id}/read` | Path | `NotificationResponse` | `backend/app/api/v1/notifications.py` | 真实联调通过 |
| 全部已读 | `notificationsApi.markAllRead` | PATCH | `/api/v1/notifications/read-all` | Bearer Token | `MarkAllReadResponse` | `backend/app/api/v1/notifications.py` | 真实联调通过 |
| 个人资料 | `usersApi.updateMe` | PATCH | `/api/v1/users/me` | JSON `UserUpdateRequest` | `UserResponse` | `backend/app/api/v1/users.py` | 真实联调通过 |
| 管理员列表 | `usersApi.list` | GET | `/api/v1/admin/users` | Query 分页 | `UserListResponse` | `backend/app/api/v1/admin.py` | 真实联调通过 |
| 启停用户 | `usersApi.updateStatus` | PATCH | `/api/v1/admin/users/{id}/status` | JSON `UserStatusRequest` | `UserResponse` | `backend/app/api/v1/admin.py` | 真实联调通过 |
| 未授权访问 | Axios 401 处理 | GET | `/api/v1/users/me` | 无效 Bearer Token | 401 业务错误 | `backend/app/api/dependencies.py` | 异常联调通过 |
| 越权访问 | Axios 403 处理 | GET | `/api/v1/admin/users` | 普通用户 Token | 403 业务错误 | `backend/app/api/dependencies.py` | 异常联调通过 |

## 已确认的接口缺口

1. 项目列表没有名称搜索、状态筛选参数。前端只筛选当前分页，并在页面明确说明。
2. 普通项目成员没有可用的全局用户搜索接口。添加成员严格使用用户 ID。
3. `ProjectResponse` 不含当前用户项目角色。前端对当前页项目查询成员列表后推导，规模增大后建议后端直接返回 `current_user_role`。
4. `UserResponse` 与管理员列表不返回系统角色。前端不能展示真实角色名称，只能依据 `/users/me/permissions` 控制当前管理员入口。
5. `ReviewCreateRequest` 没有“发起说明”字段，只有审核人和 Issue 版本；审核意见由处理接口的 `comment` 提交。
6. Review 类型通知的 `target_id` 是 Review ID，但后端没有按 Review ID 查询详情或返回对应 Issue ID，因此点击该类通知只标记已读，不做错误跳转。
