"""Review 审核流程及 Issue 状态联动服务。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConcurrentUpdateError,
    ConflictError,
    InvalidStateTransitionError,
    PermissionDeniedError,
    ResourceNotFoundError,
)
from app.core.notification_types import (
    REVIEW_APPROVED,
    REVIEW_REJECTED,
    REVIEW_REQUESTED,
)
from app.models.review import Review
from app.models.user import User
from app.repositories.issue_repository import IssueRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.issue import IssueStatus
from app.schemas.project import ProjectRoleName
from app.schemas.review import ReviewDecisionRequest, ReviewStatus
from app.tasks.notifications import enqueue_notification_delivery


class ReviewService:
    """保证 Review 处理与 Issue 状态更新处于同一事务。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.reviews = ReviewRepository(session)
        self.issues = IssueRepository(session)
        self.projects = ProjectRepository(session)
        self.notifications = NotificationRepository(session)

    async def create_review(
        self,
        issue_id: int,
        requester: User,
        reviewer_id: int,
        issue_version: int,
    ) -> Review:
        """对处理中 Issue 发起审核并原子切换为 REVIEW。"""

        issue = await self.issues.get(issue_id, for_update=True)
        if issue is None:
            raise ResourceNotFoundError("Issue 不存在")
        requester_role = await self.projects.get_member_role(
            issue.project_id,
            requester.id,
        )
        if requester_role not in {
            ProjectRoleName.OWNER.value,
            ProjectRoleName.DEVELOPER.value,
        }:
            raise PermissionDeniedError("当前项目角色不能发起 Review")
        if requester_role == ProjectRoleName.DEVELOPER.value and requester.id not in {
            issue.creator_id,
            issue.assignee_id,
        }:
            raise PermissionDeniedError("只能为自己创建或负责的 Issue 发起 Review")
        reviewer_role = await self.projects.get_member_role(
            issue.project_id,
            reviewer_id,
        )
        if reviewer_role not in {
            ProjectRoleName.OWNER.value,
            ProjectRoleName.DEVELOPER.value,
        }:
            raise ResourceNotFoundError("审核人必须是 Owner 或 Developer")
        if reviewer_id == requester.id:
            raise ConflictError("审核人不能与发起人相同")
        if issue.status != IssueStatus.IN_PROGRESS.value:
            raise InvalidStateTransitionError(
                "只有 IN_PROGRESS 状态的 Issue 可以发起 Review"
            )
        if await self.reviews.get_pending(issue.id):
            raise ConflictError("该 Issue 已存在待处理 Review")
        if issue.version != issue_version:
            raise ConcurrentUpdateError(
                "Issue 已被其他请求修改，请重新读取后再发起 Review"
            )

        try:
            review = await self.reviews.create(
                issue_id=issue.id,
                requester_id=requester.id,
                reviewer_id=reviewer_id,
            )
            issue.status = IssueStatus.REVIEW.value
            issue.version += 1
            notification = await self.notifications.create(
                user_id=reviewer_id,
                notification_type=REVIEW_REQUESTED,
                target_type="review",
                target_id=review.id,
                content=f"你收到了 Issue「{issue.title}」的 Review 请求",
            )
            await self.session.commit()
            await self.session.refresh(review)
            enqueue_notification_delivery(notification.id)
            return review
        except Exception:
            await self.session.rollback()
            raise

    async def list_reviews(
        self,
        issue_id: int,
        user: User,
    ) -> list[Review]:
        """所有项目成员均可查看 Review 历史。"""

        issue = await self.issues.get(issue_id)
        if issue is None:
            raise ResourceNotFoundError("Issue 不存在")
        if await self.projects.get_member_role(issue.project_id, user.id) is None:
            raise PermissionDeniedError("当前用户不是项目成员")
        return await self.reviews.list_by_issue(issue_id)

    async def decide_review(
        self,
        review_id: int,
        reviewer: User,
        payload: ReviewDecisionRequest,
    ) -> Review:
        """指定审核人处理一次 Review，并原子更新 Issue 状态。"""

        review = await self.reviews.get(review_id, for_update=True)
        if review is None:
            raise ResourceNotFoundError("Review 不存在")
        if review.reviewer_id != reviewer.id:
            raise PermissionDeniedError("只有指定审核人可以处理 Review")
        if review.status != ReviewStatus.PENDING.value:
            if review.status == payload.status.value:
                await self.session.commit()
                return review
            await self.session.rollback()
            raise ConflictError("该 Review 已以不同结果处理")
        issue = await self.issues.get(review.issue_id, for_update=True)
        if issue is None:
            raise ResourceNotFoundError("关联 Issue 不存在")
        if issue.status != IssueStatus.REVIEW.value:
            raise InvalidStateTransitionError("Issue 当前不处于 REVIEW 状态")

        review.status = payload.status.value
        review.comment = payload.comment
        issue.status = (
            IssueStatus.DONE.value
            if payload.status == ReviewStatus.APPROVED
            else IssueStatus.IN_PROGRESS.value
        )
        issue.version += 1
        try:
            notification = await self.notifications.create(
                user_id=review.requester_id,
                notification_type=(
                    REVIEW_APPROVED
                    if payload.status == ReviewStatus.APPROVED
                    else REVIEW_REJECTED
                ),
                target_type="review",
                target_id=review.id,
                content=(
                    f"Issue「{issue.title}」的 Review 已"
                    f"{'通过' if payload.status == ReviewStatus.APPROVED else '拒绝'}"
                ),
            )
            await self.session.commit()
            await self.session.refresh(review)
            enqueue_notification_delivery(notification.id)
            return review
        except Exception:
            await self.session.rollback()
            raise
