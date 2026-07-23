"""Issue 评论数据访问仓库。"""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment


class CommentRepository:
    """封装评论新增、查询、修改与物理删除。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        issue_id: int,
        user_id: int,
        content: str,
    ) -> Comment:
        comment = Comment(
            issue_id=issue_id,
            user_id=user_id,
            content=content,
        )
        self.session.add(comment)
        await self.session.flush()
        return comment

    async def get(self, comment_id: int) -> Comment | None:
        return (
            await self.session.execute(
                select(Comment).where(Comment.id == comment_id)
            )
        ).scalar_one_or_none()

    async def list_by_issue(self, issue_id: int) -> list[Comment]:
        result = await self.session.execute(
            select(Comment)
            .where(Comment.issue_id == issue_id)
            .order_by(Comment.id)
        )
        return list(result.scalars())

    async def delete(self, comment_id: int) -> None:
        await self.session.execute(
            delete(Comment).where(Comment.id == comment_id)
        )
