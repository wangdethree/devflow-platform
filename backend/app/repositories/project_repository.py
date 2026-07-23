"""项目、项目角色和成员数据访问仓库。"""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_role import ProjectRole
from app.models.user import User


class ProjectRepository:
    """封装项目领域持久化操作。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_project(
        self,
        *,
        name: str,
        description: str | None,
        status: str,
        owner_id: int,
    ) -> Project:
        project = Project(
            name=name,
            description=description,
            status=status,
            owner_id=owner_id,
        )
        self.session.add(project)
        await self.session.flush()
        return project

    async def get_project(self, project_id: int) -> Project | None:
        return (
            await self.session.execute(
                select(Project).where(
                    Project.id == project_id,
                    Project.is_deleted.is_(False),
                )
            )
        ).scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: int,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Project], int]:
        base_filter = (
            ProjectMember.user_id == user_id,
            Project.is_deleted.is_(False),
        )
        total = await self.session.scalar(
            select(func.count(Project.id))
            .join(
                ProjectMember,
                ProjectMember.project_id == Project.id,
            )
            .where(*base_filter)
        )
        result = await self.session.execute(
            select(Project)
            .join(
                ProjectMember,
                ProjectMember.project_id == Project.id,
            )
            .where(*base_filter)
            .order_by(Project.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars()), int(total or 0)

    async def get_role_by_name(self, name: str) -> ProjectRole | None:
        return (
            await self.session.execute(
                select(ProjectRole).where(ProjectRole.name == name)
            )
        ).scalar_one_or_none()

    async def create_member(
        self,
        *,
        project_id: int,
        user_id: int,
        role_id: int,
    ) -> ProjectMember:
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role_id=role_id,
        )
        self.session.add(member)
        await self.session.flush()
        return member

    async def get_member(
        self,
        project_id: int,
        user_id: int,
    ) -> ProjectMember | None:
        return (
            await self.session.execute(
                select(ProjectMember).where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id,
                )
            )
        ).scalar_one_or_none()

    async def get_member_role(
        self,
        project_id: int,
        user_id: int,
    ) -> str | None:
        return (
            await self.session.execute(
                select(ProjectRole.name)
                .join(
                    ProjectMember,
                    ProjectMember.role_id == ProjectRole.id,
                )
                .where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id,
                )
            )
        ).scalar_one_or_none()

    async def list_members(self, project_id: int) -> list[tuple]:
        result = await self.session.execute(
            select(ProjectMember, User, ProjectRole)
            .join(User, User.id == ProjectMember.user_id)
            .join(ProjectRole, ProjectRole.id == ProjectMember.role_id)
            .where(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.id)
        )
        return list(result.all())

    async def delete_member(self, member_id: int) -> None:
        await self.session.execute(
            delete(ProjectMember).where(ProjectMember.id == member_id)
        )
