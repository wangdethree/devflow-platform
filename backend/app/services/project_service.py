"""项目、成员和项目级权限业务服务。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    PermissionDeniedError,
    ResourceNotFoundError,
)
from app.core.notification_types import PROJECT_MEMBER_ADDED
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectMemberCreateRequest,
    ProjectMemberResponse,
    ProjectMemberUpdateRequest,
    ProjectRoleName,
    ProjectUpdateRequest,
)
from app.tasks.notifications import enqueue_notification_delivery


class ProjectService:
    """集中维护项目权限与项目成员业务规则。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.projects = ProjectRepository(session)
        self.users = UserRepository(session)
        self.notifications = NotificationRepository(session)

    async def require_project(
        self,
        project_id: int,
        user_id: int,
        *,
        allowed_roles: set[str] | None = None,
    ) -> Project:
        """校验项目存在、成员身份以及可选项目角色。"""

        project = await self.projects.get_project(project_id)
        if project is None:
            raise ResourceNotFoundError("项目不存在")
        role = await self.projects.get_member_role(project_id, user_id)
        if role is None:
            raise PermissionDeniedError("当前用户不是项目成员")
        if allowed_roles is not None and role not in allowed_roles:
            raise PermissionDeniedError("当前项目角色没有该操作权限")
        return project

    async def create_project(
        self,
        creator: User,
        payload: ProjectCreateRequest,
    ) -> Project:
        """原子创建项目并将创建者写入 Owner 成员关系。"""

        owner_role = await self.projects.get_role_by_name(
            ProjectRoleName.OWNER.value
        )
        if owner_role is None:
            raise ConflictError("项目角色尚未初始化，请先执行 seed 命令")

        try:
            project = await self.projects.create_project(
                name=payload.name.strip(),
                description=payload.description,
                status=payload.status.value,
                owner_id=creator.id,
            )
            await self.projects.create_member(
                project_id=project.id,
                user_id=creator.id,
                role_id=owner_role.id,
            )
            await self.session.commit()
            await self.session.refresh(project)
            return project
        except Exception:
            await self.session.rollback()
            raise

    async def get_project(self, project_id: int, user: User) -> Project:
        """返回当前成员有权访问的项目。"""

        return await self.require_project(project_id, user.id)

    async def list_projects(
        self,
        user: User,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Project], int]:
        """返回当前用户参与且未删除的项目。"""

        return await self.projects.list_for_user(
            user.id,
            page=page,
            page_size=page_size,
        )

    async def update_project(
        self,
        project_id: int,
        user: User,
        payload: ProjectUpdateRequest,
    ) -> Project:
        """仅 Owner 可以修改项目基础信息。"""

        project = await self.require_project(
            project_id,
            user.id,
            allowed_roles={ProjectRoleName.OWNER.value},
        )
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, field, value.value if hasattr(value, "value") else value)
        try:
            await self.session.commit()
            await self.session.refresh(project)
            return project
        except Exception:
            await self.session.rollback()
            raise

    async def delete_project(self, project_id: int, user: User) -> None:
        """仅 Owner 可以软删除项目。"""

        project = await self.require_project(
            project_id,
            user.id,
            allowed_roles={ProjectRoleName.OWNER.value},
        )
        project.is_deleted = True
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def add_member(
        self,
        project_id: int,
        operator: User,
        payload: ProjectMemberCreateRequest,
    ) -> ProjectMemberResponse:
        """Owner 添加有效用户并分配项目角色。"""

        await self.require_project(
            project_id,
            operator.id,
            allowed_roles={ProjectRoleName.OWNER.value},
        )
        user = await self.users.get_by_id(payload.user_id)
        if user is None or not user.is_active:
            raise ResourceNotFoundError("待添加用户不存在或不可用")
        if await self.projects.get_member(project_id, payload.user_id):
            raise ConflictError("该用户已经是项目成员")
        role = await self.projects.get_role_by_name(payload.role.value)
        if role is None:
            raise ResourceNotFoundError("项目角色不存在")

        try:
            member = await self.projects.create_member(
                project_id=project_id,
                user_id=user.id,
                role_id=role.id,
            )
            # 成员关系与邀请通知共同提交，避免成员已加入但通知丢失。
            notification = await self.notifications.create(
                user_id=user.id,
                notification_type=PROJECT_MEMBER_ADDED,
                target_type="project",
                target_id=project_id,
                content=f"你已加入项目，项目角色为 {role.name}",
            )
            await self.session.commit()
            await self.session.refresh(member)
            enqueue_notification_delivery(notification.id)
        except Exception:
            await self.session.rollback()
            raise
        return self._member_response(member, user, role.name)

    async def list_members(
        self,
        project_id: int,
        user: User,
    ) -> list[ProjectMemberResponse]:
        """所有项目成员均可查询成员列表。"""

        await self.require_project(project_id, user.id)
        rows = await self.projects.list_members(project_id)
        return [
            self._member_response(member, member_user, role.name)
            for member, member_user, role in rows
        ]

    async def update_member(
        self,
        project_id: int,
        member_user_id: int,
        operator: User,
        payload: ProjectMemberUpdateRequest,
    ) -> ProjectMemberResponse:
        """Owner 修改成员角色，主负责人必须始终保留 Owner 身份。"""

        project = await self.require_project(
            project_id,
            operator.id,
            allowed_roles={ProjectRoleName.OWNER.value},
        )
        member = await self.projects.get_member(project_id, member_user_id)
        if member is None:
            raise ResourceNotFoundError("项目成员不存在")
        if (
            member_user_id == project.owner_id
            and payload.role != ProjectRoleName.OWNER
        ):
            raise ConflictError("不能修改项目主负责人的 Owner 角色")
        role = await self.projects.get_role_by_name(payload.role.value)
        member_user = await self.users.get_by_id(member_user_id)
        if role is None or member_user is None:
            raise ResourceNotFoundError("用户或项目角色不存在")
        member.role_id = role.id
        try:
            await self.session.commit()
            await self.session.refresh(member)
        except Exception:
            await self.session.rollback()
            raise
        return self._member_response(member, member_user, role.name)

    async def remove_member(
        self,
        project_id: int,
        member_user_id: int,
        operator: User,
    ) -> None:
        """Owner 移除普通成员，但不能移除项目主负责人。"""

        project = await self.require_project(
            project_id,
            operator.id,
            allowed_roles={ProjectRoleName.OWNER.value},
        )
        if member_user_id == project.owner_id:
            raise ConflictError("不能移除项目主负责人")
        member = await self.projects.get_member(project_id, member_user_id)
        if member is None:
            raise ResourceNotFoundError("项目成员不存在")
        try:
            await self.projects.delete_member(member.id)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    @staticmethod
    def _member_response(
        member: ProjectMember,
        user: User,
        role_name: str,
    ) -> ProjectMemberResponse:
        return ProjectMemberResponse(
            id=member.id,
            project_id=member.project_id,
            user_id=user.id,
            username=user.username,
            email=user.email,
            role=role_name,
            joined_at=member.joined_at,
        )
