"""User repository for managing Telegram bot users."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User
from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        result = await self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def create_or_update_from_telegram(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None
    ) -> User:
        """Create or update user from Telegram data."""
        user = await self.get_by_telegram_id(telegram_id)
        
        if user:
            # Update existing user
            update_data = {}
            if username is not None:
                update_data["telegram_username"] = username
            if first_name is not None:
                update_data["first_name"] = first_name
            if last_name is not None:
                update_data["last_name"] = last_name
            if language_code is not None:
                update_data["language_code"] = language_code
            
            if update_data:
                user = await self.update_by_id(user.id, **update_data)
        else:
            # Create new user
            user = await self.create(
                telegram_id=telegram_id,
                telegram_username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code
            )
        
        return user
    
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
        update_data = {}
        if daily_word_count is not None:
            update_data["daily_word_count"] = daily_word_count
        if difficulty_level is not None:
            update_data["difficulty_level"] = difficulty_level
        if preferred_time is not None:
            update_data["preferred_time"] = preferred_time
        if timezone is not None:
            update_data["timezone"] = timezone
        if notifications_enabled is not None:
            update_data["notifications_enabled"] = notifications_enabled
        
        if update_data:
            return await self.update_by_id(user_id, **update_data)
        return await self.get_by_id(user_id)
    
    async def update_notion_settings(
        self,
        user_id: int,
        notion_token: Optional[str] = None,
        notion_database_id: Optional[str] = None,
        notion_enabled: Optional[bool] = None
    ) -> Optional[User]:
        """Update user Notion integration settings."""
        update_data = {}
        if notion_token is not None:
            update_data["notion_token"] = notion_token
        if notion_database_id is not None:
            update_data["notion_database_id"] = notion_database_id
        if notion_enabled is not None:
            update_data["notion_enabled"] = notion_enabled
        
        if update_data:
            return await self.update_by_id(user_id, **update_data)
        return await self.get_by_id(user_id) 