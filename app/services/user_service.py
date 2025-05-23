"""User service for managing user accounts and preferences."""

import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.repositories.user import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management and preferences."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def get_or_create_user_from_telegram(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None
    ) -> User:
        """Get or create user from Telegram data."""
        return await self.user_repo.create_or_update_from_telegram(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code
        )
    
    async def update_user_activity(self, user_id: int) -> Optional[User]:
        """Update user's last activity timestamp."""
        return await self.user_repo.update_by_id(
            user_id, 
            last_activity=datetime.utcnow()
        )
    
    async def update_learning_preferences(
        self,
        user_id: int,
        daily_word_count: Optional[int] = None,
        difficulty_level: Optional[str] = None,
        preferred_time: Optional[str] = None,
        timezone: Optional[str] = None,
        notifications_enabled: Optional[bool] = None
    ) -> Optional[User]:
        """Update user learning preferences."""
        return await self.user_repo.update_learning_preferences(
            user_id=user_id,
            daily_word_count=daily_word_count,
            difficulty_level=difficulty_level,
            preferred_time=preferred_time,
            timezone=timezone,
            notifications_enabled=notifications_enabled
        )
    
    async def increment_learning_streak(self, user_id: int) -> Optional[User]:
        """Increment user's learning streak."""
        user = await self.user_repo.get_by_id(user_id)
        if user:
            return await self.user_repo.update_by_id(
                user_id,
                learning_streak=user.learning_streak + 1
            )
        return None
    
    async def reset_learning_streak(self, user_id: int) -> Optional[User]:
        """Reset user's learning streak to 0."""
        return await self.user_repo.update_by_id(user_id, learning_streak=0)
    
    async def increment_words_learned(self, user_id: int, count: int = 1) -> Optional[User]:
        """Increment user's total words learned count."""
        user = await self.user_repo.get_by_id(user_id)
        if user:
            return await self.user_repo.update_by_id(
                user_id,
                total_words_learned=user.total_words_learned + count
            )
        return None
    
    async def update_daily_words_sent(self, user_id: int) -> Optional[User]:
        """Update timestamp when daily words were last sent."""
        return await self.user_repo.update_by_id(
            user_id,
            last_daily_words_sent=datetime.utcnow()
        )
    
    async def setup_notion_integration(
        self,
        user_id: int,
        notion_token: str,
        notion_database_id: Optional[str] = None
    ) -> Optional[User]:
        """Setup Notion integration for a user."""
        return await self.user_repo.update_notion_settings(
            user_id=user_id,
            notion_token=notion_token,
            notion_database_id=notion_database_id,
            notion_enabled=True
        )
    
    async def disable_notion_integration(self, user_id: int) -> Optional[User]:
        """Disable Notion integration for a user."""
        return await self.user_repo.update_notion_settings(
            user_id=user_id,
            notion_enabled=False
        )
    
    async def get_user_statistics(self, user_id: int) -> Optional[dict]:
        """Get comprehensive user statistics."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        # You can extend this with more complex statistics
        # by querying word progress, review history, etc.
        
        return {
            "user_id": user.id,
            "display_name": user.display_name,
            "difficulty_level": user.difficulty_level,
            "daily_word_count": user.daily_word_count,
            "learning_streak": user.learning_streak,
            "total_words_learned": user.total_words_learned,
            "is_premium": user.is_premium,
            "notion_enabled": user.notion_enabled,
            "created_at": user.created_at,
            "last_activity": user.last_activity,
            "last_daily_words_sent": user.last_daily_words_sent
        } 