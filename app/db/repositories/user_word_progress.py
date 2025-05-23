"""User word progress repository for SRS learning management."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user_word_progress import UserWordProgress
from app.db.repositories.base import BaseRepository


class UserWordProgressRepository(BaseRepository[UserWordProgress]):
    """Repository for UserWordProgress model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(UserWordProgress, db)
    
    async def get_by_user_and_word(self, user_id: int, word_id: int) -> Optional[UserWordProgress]:
        """Get progress for specific user and word."""
        result = await self.db.execute(
            select(UserWordProgress).where(
                and_(
                    UserWordProgress.user_id == user_id,
                    UserWordProgress.word_id == word_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_progress_by_status(self, user_id: int, status: str) -> List[UserWordProgress]:
        """Get user's progress by learning status."""
        result = await self.db.execute(
            select(UserWordProgress).where(
                and_(
                    UserWordProgress.user_id == user_id,
                    UserWordProgress.status == status
                )
            ).order_by(UserWordProgress.next_review_at)
        )
        return list(result.scalars().all())
    
    async def get_words_due_for_review(self, user_id: int) -> List[UserWordProgress]:
        """Get words due for review for a user."""
        result = await self.db.execute(
            select(UserWordProgress).where(
                and_(
                    UserWordProgress.user_id == user_id,
                    UserWordProgress.next_review_at <= datetime.utcnow()
                )
            ).order_by(UserWordProgress.next_review_at)
        )
        return list(result.scalars().all())
    
    async def create_or_get_progress(self, user_id: int, word_id: int) -> UserWordProgress:
        """Create or get existing progress for user and word."""
        progress = await self.get_by_user_and_word(user_id, word_id)
        if not progress:
            progress = await self.create(user_id=user_id, word_id=word_id)
        return progress 