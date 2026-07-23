"""Issue 业务规则、筛选和状态流转服务。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidStateTransitionError,
    PermissionDeniedError,
    ResourceNotFoundError,
)
from app.core.notification_types import ISSUE_ASSIGNED, ISSUE_STATUS_CHANGED
from app.models.issue import Issue
from app.models.user import User
from app.repositories.issue_repository import IssueRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.issue import (
    IssueCreateRequest,
    IssueStatus,
    IssueUpdateRequest,
)
from app.schemas.project import ProjectRoleName
from app.tasks.notifications import enqueue_notification_delivery


ALLOWED_TRANSITIONS = {
    IssueStatus.OPEN.value: {IssueStatus.IN_PROGRESS.value},
    IssueStatus.IN_PROGRESS.value: {IssueStatus.REVIEW.value},
    IssueStatus.REVIEW.value: {IssueStatus.DONE.value},
    IssueStatus.DONE.value: set(),
}


class IssueService:
    """集中维护 Issue 数据范围、写权限和状态机。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.issues = IssueRepository(session)
        self.projects = ProjectRepository(session)
        self.notifications = NotificationRepository(session)

    async def require_issue(self, issue_id: int, user: User) -> Issue:
        """校验 Issue 存在且当前用户属于对应项目。"""

        issue = await self.issues.get(issue_id)
        if issue is None:
            raise ResourceNotFoundError("Issue 不存在")
        role = await self.projects.get_member_role(issue.project_id, user.id)
        if role is None:
            raise PermissionDeniedError("当前用户不是项目成员")
        return issue

    async def _require_write(self, issue: Issue, user: User) -> str:
        """Owner 可管理全部 Issue，Developer 仅处理自己创建或负责的 Issue。"""

        role = await self.projects.get_member_role(issue.project_id, user.id)
        if role == ProjectRoleName.OWNER.value:
            return role
        if role == ProjectRoleName.DEVELOPER.value and user.id in {
            issue.creator_id,
            issue.assignee_id,
        }:
            return role
        raise PermissionDeniedError("当前成员无权修改该 Issue")

    async def _validate_assignee(
        self,
        project_id: int,
        assignee_id: int | None,
    ) -> None:
        if assignee_id is None:
            return
        if await self.projects.get_member(project_id, assignee_id) is None:
            raise ResourceNotFoundError("Issue 负责人必须是项目成员")

    async def create_issue(
        self,
        project_id: int,
        creator: User,
        payload: IssueCreateRequest,
    ) -> Issue:
        """Owner 或 Developer 创建 Issue，Viewer 保持只读。"""

        role = await self.projects.get_member_role(project_id, creator.id)
        if role not in {
            ProjectRoleName.OWNER.value,
            ProjectRoleName.DEVELOPER.value,
        }:
            raise PermissionDeniedError("当前项目角色不能创建 Issue")
        project = await self.projects.get_project(project_id)
        if project is None:
            raise ResourceNotFoundError("项目不存在")
        await self._validate_assignee(project_id, payload.assignee_id)

        try:
            notification = None
            issue = await self.issues.create(
                project_id=project_id,
                creator_id=creator.id,
                assignee_id=payload.assignee_id,
                title=payload.title.strip(),
                description=payload.description,
                issue_type=payload.type.value,
                priority=payload.priority.value,
            )
            if issue.assignee_id is not None:
                notification = await self.notifications.create(
                    user_id=issue.assignee_id,
                    notification_type=ISSUE_ASSIGNED,
                    target_type="issue",
                    target_id=issue.id,
                    content=f"Issue「{issue.title}」已分配给你",
                )
            await self.session.commit()
            await self.session.refresh(issue)
            if notification is not None:
                enqueue_notification_delivery(notification.id)
            return issue
        except Exception:
            await self.session.rollback()
            raise

    async def list_issues(
        self,
        user: User,
        **filters,
    ) -> tuple[list[Issue], int]:
        """仅返回当前用户所参与项目中的未删除 Issue。"""

        return await self.issues.list_for_user(user.id, **filters)

    async def get_issue(self, issue_id: int, user: User) -> Issue:
        """返回成员可访问的 Issue 详情。"""

        return await self.require_issue(issue_id, user)

    async def update_issue(
        self,
        issue_id: int,
        user: User,
        payload: IssueUpdateRequest,
    ) -> Issue:
        """更新 Issue 基础字段，状态必须走专用状态接口。"""

        issue = await self.require_issue(issue_id, user)
        await self._require_write(issue, user)
        data = payload.model_dump(exclude_unset=True)
        old_assignee_id = issue.assignee_id
        if "assignee_id" in data:
            await self._validate_assignee(issue.project_id, data["assignee_id"])
        for field, value in data.items():
            setattr(issue, field, value.value if hasattr(value, "value") else value)
        try:
            notification = None
            if (
                "assignee_id" in data
                and issue.assignee_id is not None
                and issue.assignee_id != old_assignee_id
            ):
                notification = await self.notifications.create(
                    user_id=issue.assignee_id,
                    notification_type=ISSUE_ASSIGNED,
                    target_type="issue",
                    target_id=issue.id,
                    content=f"Issue「{issue.title}」已分配给你",
                )
            await self.session.commit()
            await self.session.refresh(issue)
            if notification is not None:
                enqueue_notification_delivery(notification.id)
            return issue
        except Exception:
            await self.session.rollback()
            raise

    async def transition_status(
        self,
        issue_id: int,
        user: User,
        target_status: IssueStatus,
    ) -> Issue:
        """按 OPEN→IN_PROGRESS→REVIEW→DONE 顺序流转状态。"""

        issue = await self.require_issue(issue_id, user)
        await self._require_write(issue, user)
        allowed = ALLOWED_TRANSITIONS.get(issue.status, set())
        if target_status.value not in allowed:
            raise InvalidStateTransitionError(
                f"不允许从 {issue.status} 流转到 {target_status.value}"
            )
        issue.status = target_status.value
        try:
            notification = None
            if issue.assignee_id is not None:
                notification = await self.notifications.create(
                    user_id=issue.assignee_id,
                    notification_type=ISSUE_STATUS_CHANGED,
                    target_type="issue",
                    target_id=issue.id,
                    content=f"Issue「{issue.title}」状态已更新为 {issue.status}",
                )
            await self.session.commit()
            await self.session.refresh(issue)
            if notification is not None:
                enqueue_notification_delivery(notification.id)
            return issue
        except Exception:
            await self.session.rollback()
            raise

    async def delete_issue(self, issue_id: int, user: User) -> None:
        """Owner 或授权 Developer 软删除 Issue。"""

        issue = await self.require_issue(issue_id, user)
        await self._require_write(issue, user)
        issue.is_deleted = True
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
