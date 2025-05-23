"""
Word model for caching LLM-generated vocabulary words.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Integer, String, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Word(Base):
    """Word model for caching LLM-generated vocabulary."""
    
    __tablename__ = "words"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Core word information (LLM-generated)
    english_word: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    turkish_translation: Mapped[str] = mapped_column(String(500), nullable=False)
    part_of_speech: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Additional LLM-generated content
    definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pronunciation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    difficulty_level: Mapped[str] = mapped_column(String(50), nullable=False, default="B1_B2")
    
    # LLM generation metadata
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    llm_model: Mapped[str] = mapped_column(String(100), nullable=False)
    llm_prompt_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA-256 hash
    llm_response_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA-256 hash
    
    # Content validation and quality
    is_verified: Mapped[bool] = mapped_column(default=False)
    quality_score: Mapped[Optional[float]] = mapped_column(nullable=True)  # 0.0 - 1.0
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Oxford 3000 metadata
    oxford_3000_level: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # A1, A2, B1, B2
    word_frequency_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
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
    last_llm_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    examples: Mapped[list["Example"]] = relationship(
        "Example",
        back_populates="word",
        cascade="all, delete-orphan"
    )
    user_progress: Mapped[list["UserWordProgress"]] = relationship(
        "UserWordProgress",
        back_populates="word",
        cascade="all, delete-orphan"
    )
    
    # Database indexes for performance
    __table_args__ = (
        Index("idx_word_difficulty", "difficulty_level"),
        Index("idx_word_oxford_level", "oxford_3000_level"),
        Index("idx_word_verified", "is_verified"),
        Index("idx_word_usage", "usage_count"),
        Index("idx_word_english_lower", func.lower("english_word")),
    )
    
    def __repr__(self) -> str:
        return f"<Word(id={self.id}, english_word='{self.english_word}', pos='{self.part_of_speech}')>"
    
    def to_dict(self) -> dict:
        """Convert word to dictionary for API responses."""
        return {
            "id": self.id,
            "english_word": self.english_word,
            "turkish_translation": self.turkish_translation,
            "part_of_speech": self.part_of_speech,
            "definition": self.definition,
            "pronunciation": self.pronunciation,
            "difficulty_level": self.difficulty_level,
            "oxford_3000_level": self.oxford_3000_level,
            "is_verified": self.is_verified,
            "quality_score": self.quality_score,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def increment_usage(self) -> None:
        """Increment usage count and update last used timestamp."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow() 