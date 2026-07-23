"""Issue 查询、筛选、分页与持久化仓库。"""

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.issue import Issue
from app.models.project_member import ProjectMember


class IssueRepository:
    """封装 Issue 数据访问，不判断项目角色与状态流转。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        project_id: int,
        creator_id: int,
        assignee_id: int | None,
        title: str,
        description: str | None,
        issue_type: str,
        priority: str,
    ) -> Issue:
        issue = Issue(
            project_id=project_id,
            creator_id=creator_id,
            assignee_id=assignee_id,
            title=title,
            description=description,
            type=issue_type,
            priority=priority,
            status="OPEN",
        )
        self.session.add(issue)
        await self.session.flush()
        return issue

    async def get(
        self,
        issue_id: int,
        *,
        for_update: bool = False,
    ) -> Issue | None:
        statement = select(Issue).where(
            Issue.id == issue_id,
            Issue.is_deleted.is_(False),
        )
        if for_update:
            statement = statement.with_for_update()
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def update_with_version(
        self,
        issue_id: int,
        expected_version: int,
        values: dict,
    ) -> bool:
        """仅当版本匹配时更新，并在数据库中原子递增版本号。"""

        result = await self.session.execute(
            update(Issue)
            .where(
                Issue.id == issue_id,
                Issue.version == expected_version,
                Issue.is_deleted.is_(False),
            )
            .values(
                **values,
                version=Issue.version + 1,
                updated_at=func.now(),
            )
        )
        return bool(result.rowcount)

    async def list_for_user(
        self,
        user_id: int,
        *,
        project_id: int | None,
        creator_id: int | None,
        assignee_id: int | None,
        status: str | None,
        issue_type: str | None,
        priority: str | None,
        keyword: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Issue], int]:
        filters = [
            ProjectMember.user_id == user_id,
            ProjectMember.project_id == Issue.project_id,
            Issue.is_deleted.is_(False),
        ]
        if project_id is not None:
            filters.append(Issue.project_id == project_id)
        if creator_id is not None:
            filters.append(Issue.creator_id == creator_id)
        if assignee_id is not None:
            filters.append(Issue.assignee_id == assignee_id)
        if status is not None:
            filters.append(Issue.status == status)
        if issue_type is not None:
            filters.append(Issue.type == issue_type)
        if priority is not None:
            filters.append(Issue.priority == priority)
        if keyword:
            pattern = f"%{keyword.strip()}%"
            filters.append(
                or_(
                    Issue.title.like(pattern),
                    Issue.description.like(pattern),
                )
            )

        total = await self.session.scalar(
            select(func.count(Issue.id))
            .join(
                ProjectMember,
                ProjectMember.project_id == Issue.project_id,
            )
            .where(*filters)
        )
        result = await self.session.execute(
            select(Issue)
            .join(
                ProjectMember,
                ProjectMember.project_id == Issue.project_id,
            )
            .where(*filters)
            .order_by(Issue.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars()), int(total or 0)
