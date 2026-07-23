"""Issue Review 数据访问仓库。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review


class ReviewRepository:
    """封装 Review 的新增、查询和历史读取。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        issue_id: int,
        requester_id: int,
        reviewer_id: int,
    ) -> Review:
        review = Review(
            issue_id=issue_id,
            requester_id=requester_id,
            reviewer_id=reviewer_id,
            status="PENDING",
        )
        self.session.add(review)
        await self.session.flush()
        return review

    async def get(self, review_id: int) -> Review | None:
        return (
            await self.session.execute(
                select(Review).where(Review.id == review_id)
            )
        ).scalar_one_or_none()

    async def get_pending(self, issue_id: int) -> Review | None:
        return (
            await self.session.execute(
                select(Review).where(
                    Review.issue_id == issue_id,
                    Review.status == "PENDING",
                )
            )
        ).scalar_one_or_none()

    async def list_by_issue(self, issue_id: int) -> list[Review]:
        result = await self.session.execute(
            select(Review)
            .where(Review.issue_id == issue_id)
            .order_by(Review.id.desc())
        )
        return list(result.scalars())
