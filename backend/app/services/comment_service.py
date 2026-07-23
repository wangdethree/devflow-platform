"""Issue 评论业务与作者权限服务。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError
from app.models.comment import Comment
from app.models.user import User
from app.repositories.comment_repository import CommentRepository
from app.repositories.issue_repository import IssueRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectRoleName


class CommentService:
    """维护评论的项目成员范围和作者操作规则。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.comments = CommentRepository(session)
        self.issues = IssueRepository(session)
        self.projects = ProjectRepository(session)

    async def _require_issue_member(
        self,
        issue_id: int,
        user_id: int,
    ) -> tuple:
        issue = await self.issues.get(issue_id)
        if issue is None:
            raise ResourceNotFoundError("Issue 不存在")
        role = await self.projects.get_member_role(issue.project_id, user_id)
        if role is None:
            raise PermissionDeniedError("当前用户不是项目成员")
        return issue, role

    async def create_comment(
        self,
        issue_id: int,
        user: User,
        content: str,
    ) -> Comment:
        """Owner 和 Developer 可以发表评论，Viewer 只读。"""

        _, role = await self._require_issue_member(issue_id, user.id)
        if role == ProjectRoleName.VIEWER.value:
            raise PermissionDeniedError("Viewer 不能发表评论")
        try:
            comment = await self.comments.create(
                issue_id=issue_id,
                user_id=user.id,
                content=content.strip(),
            )
            await self.session.commit()
            await self.session.refresh(comment)
            return comment
        except Exception:
            await self.session.rollback()
            raise

    async def list_comments(
        self,
        issue_id: int,
        user: User,
    ) -> list[Comment]:
        """所有项目成员均可查看评论。"""

        await self._require_issue_member(issue_id, user.id)
        return await self.comments.list_by_issue(issue_id)

    async def update_comment(
        self,
        comment_id: int,
        user: User,
        content: str,
    ) -> Comment:
        """用户只能修改自己的评论。"""

        comment = await self.comments.get(comment_id)
        if comment is None:
            raise ResourceNotFoundError("评论不存在")
        await self._require_issue_member(comment.issue_id, user.id)
        if comment.user_id != user.id:
            raise PermissionDeniedError("只能修改自己的评论")
        comment.content = content.strip()
        try:
            await self.session.commit()
            await self.session.refresh(comment)
            return comment
        except Exception:
            await self.session.rollback()
            raise

    async def delete_comment(self, comment_id: int, user: User) -> None:
        """用户只能物理删除自己的评论。"""

        comment = await self.comments.get(comment_id)
        if comment is None:
            raise ResourceNotFoundError("评论不存在")
        await self._require_issue_member(comment.issue_id, user.id)
        if comment.user_id != user.id:
            raise PermissionDeniedError("只能删除自己的评论")
        try:
            await self.comments.delete(comment.id)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
