"""
User model for storing user information and preferences.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
from app.core.config import settings


class User(Base):
    """User model for Telegram bot users."""
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Telegram information
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="en")
    
    # User preferences
    daily_word_count: Mapped[int] = mapped_column(Integer, default=settings.daily_word_count)
    difficulty_level: Mapped[str] = mapped_column(String(50), default=settings.oxford_3000_difficulty)
    learning_streak: Mapped[int] = mapped_column(Integer, default=0)
    total_words_learned: Mapped[int] = mapped_column(Integer, default=0)
    
    # Notification settings
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    preferred_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # HH:MM format
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Notion integration
    notion_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notion_database_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notion_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_activity: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_daily_words_sent: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    word_progress: Mapped[list["UserWordProgress"]] = relationship(
        "UserWordProgress",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.telegram_username})>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        names = [self.first_name, self.last_name]
        return " ".join(name for name in names if name)
    
    @property
    def display_name(self) -> str:
        """Get user's display name (full name or username)."""
        full_name = self.full_name
        if full_name:
            return full_name
        return self.telegram_username or f"User {self.telegram_id}" 