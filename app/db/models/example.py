"""
Example model for caching LLM-generated example sentences.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Example(Base):
    """Example model for caching LLM-generated example sentences."""
    
    __tablename__ = "examples"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to word
    word_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("words.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Core example content (LLM-generated)
    english_sentence: Mapped[str] = mapped_column(Text, nullable=False)
    turkish_translation: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Context and metadata
    context_hint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty_level: Mapped[str] = mapped_column(String(50), nullable=False, default="B1_B2")
    sentence_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # declarative, question, etc.
    
    # LLM generation metadata
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    llm_model: Mapped[str] = mapped_column(String(100), nullable=False)
    llm_prompt_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA-256 hash
    llm_response_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA-256 hash
    
    # Content validation and quality
    is_verified: Mapped[bool] = mapped_column(default=False)
    quality_score: Mapped[Optional[float]] = mapped_column(nullable=True)  # 0.0 - 1.0
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Linguistic features
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    complexity_score: Mapped[Optional[float]] = mapped_column(nullable=True)  # 0.0 - 1.0
    
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
    word: Mapped["Word"] = relationship(
        "Word",
        back_populates="examples"
    )
    
    # Database indexes for performance
    __table_args__ = (
        Index("idx_example_word_id", "word_id"),
        Index("idx_example_difficulty", "difficulty_level"),
        Index("idx_example_verified", "is_verified"),
        Index("idx_example_usage", "usage_count"),
        Index("idx_example_quality", "quality_score"),
    )
    
    def __repr__(self) -> str:
        return f"<Example(id={self.id}, word_id={self.word_id}, sentence='{self.english_sentence[:50]}...')>"
    
    def to_dict(self) -> dict:
        """Convert example to dictionary for API responses."""
        return {
            "id": self.id,
            "word_id": self.word_id,
            "english_sentence": self.english_sentence,
            "turkish_translation": self.turkish_translation,
            "context_hint": self.context_hint,
            "difficulty_level": self.difficulty_level,
            "sentence_type": self.sentence_type,
            "is_verified": self.is_verified,
            "quality_score": self.quality_score,
            "usage_count": self.usage_count,
            "word_count": self.word_count,
            "complexity_score": self.complexity_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def increment_usage(self) -> None:
        """Increment usage count and update last used timestamp."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
    
    @property
    def preview(self) -> str:
        """Get a preview of the example sentence."""
        if len(self.english_sentence) <= 100:
            return self.english_sentence
        return self.english_sentence[:97] + "..." 