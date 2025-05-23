"""
User word progress model for tracking learning progress with SRS.
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import (
    DateTime, ForeignKey, Integer, String, Float, Boolean, 
    func, Index, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class UserWordProgress(Base):
    """User word progress model with Spaced Repetition System (SRS)."""
    
    __tablename__ = "user_word_progress"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    word_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("words.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Learning status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="new"  # new, learning, review, mastered, failed
    )
    
    # SRS data
    srs_level: Mapped[int] = mapped_column(Integer, default=0)  # SRS interval level
    srs_interval: Mapped[int] = mapped_column(Integer, default=1)  # Days until next review
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)  # Ease factor for SRS
    
    # Performance metrics
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    correct_reviews: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_correct: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_incorrect: Mapped[int] = mapped_column(Integer, default=0)
    
    # Detailed performance tracking
    accuracy_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0.0 - 1.0
    average_response_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # seconds
    difficulty_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 scale
    
    # Learning milestones
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    first_correct_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    mastered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Review scheduling
    next_review_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now
    )
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # User interaction data
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)  # For difficult words
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # System timestamps
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
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="word_progress")
    word: Mapped["Word"] = relationship("Word", back_populates="user_progress")
    
    # Database constraints and indexes
    __table_args__ = (
        Index("idx_user_word_unique", "user_id", "word_id", unique=True),
        Index("idx_next_review", "next_review_at"),
        Index("idx_status", "status"),
        Index("idx_srs_level", "srs_level"),
        Index("idx_user_status", "user_id", "status"),
        CheckConstraint("srs_level >= 0", name="check_srs_level_positive"),
        CheckConstraint("srs_interval >= 1", name="check_srs_interval_positive"),
        CheckConstraint("ease_factor >= 1.0", name="check_ease_factor_minimum"),
        CheckConstraint("accuracy_rate >= 0.0 AND accuracy_rate <= 1.0", name="check_accuracy_rate_range"),
        CheckConstraint("difficulty_rating >= 1 AND difficulty_rating <= 5", name="check_difficulty_rating_range"),
    )
    
    def __repr__(self) -> str:
        return f"<UserWordProgress(user_id={self.user_id}, word_id={self.word_id}, status='{self.status}')>"
    
    def calculate_accuracy_rate(self) -> float:
        """Calculate and update accuracy rate."""
        if self.total_reviews == 0:
            return 0.0
        accuracy = self.correct_reviews / self.total_reviews
        self.accuracy_rate = accuracy
        return accuracy
    
    def record_review(self, is_correct: bool, response_time: Optional[float] = None, 
                     difficulty: Optional[int] = None) -> None:
        """Record a review attempt and update SRS parameters."""
        self.total_reviews += 1
        self.last_reviewed_at = datetime.utcnow()
        
        if is_correct:
            self.correct_reviews += 1
            self.consecutive_correct += 1
            self.consecutive_incorrect = 0
            
            if not self.first_correct_at:
                self.first_correct_at = datetime.utcnow()
                
            # Update SRS for correct answer
            self._update_srs_success()
            
        else:
            self.consecutive_incorrect += 1
            self.consecutive_correct = 0
            
            # Update SRS for incorrect answer
            self._update_srs_failure()
        
        # Update performance metrics
        self.calculate_accuracy_rate()
        
        if response_time is not None:
            if self.average_response_time is None:
                self.average_response_time = response_time
            else:
                # Exponential moving average
                self.average_response_time = 0.8 * self.average_response_time + 0.2 * response_time
        
        if difficulty is not None:
            self.difficulty_rating = difficulty
            
        # Update status based on performance
        self._update_status()
        
        # Schedule next review
        self._schedule_next_review()
    
    def _update_srs_success(self) -> None:
        """Update SRS parameters for successful review."""
        if self.srs_level == 0:
            self.srs_level = 1
            self.srs_interval = 1
        elif self.srs_level == 1:
            self.srs_level = 2
            self.srs_interval = 6
        else:
            self.srs_level += 1
            self.srs_interval = int(self.srs_interval * self.ease_factor)
        
        # Increase ease factor for consecutive correct answers
        if self.consecutive_correct >= 2:
            self.ease_factor = min(self.ease_factor + 0.1, 3.0)
    
    def _update_srs_failure(self) -> None:
        """Update SRS parameters for failed review."""
        self.srs_level = max(0, self.srs_level - 1)
        self.srs_interval = 1
        
        # Decrease ease factor for consecutive incorrect answers
        if self.consecutive_incorrect >= 2:
            self.ease_factor = max(self.ease_factor - 0.2, 1.3)
    
    def _update_status(self) -> None:
        """Update learning status based on performance."""
        if self.status == "new" and self.total_reviews > 0:
            self.status = "learning"
        
        # Mastery criteria: high accuracy and high SRS level
        if (self.accuracy_rate and self.accuracy_rate >= 0.9 and 
            self.srs_level >= 5 and self.consecutive_correct >= 3):
            self.status = "mastered"
            if not self.mastered_at:
                self.mastered_at = datetime.utcnow()
        
        # Reset from mastered if performance drops
        elif self.status == "mastered" and self.consecutive_incorrect >= 2:
            self.status = "review"
        
        # Mark as failed if consistently performing poorly
        elif (self.total_reviews >= 5 and self.accuracy_rate and 
              self.accuracy_rate < 0.3 and self.consecutive_incorrect >= 3):
            self.status = "failed"
    
    def _schedule_next_review(self) -> None:
        """Schedule the next review based on SRS interval."""
        if self.status == "mastered":
            # Longer intervals for mastered words
            self.next_review_at = datetime.utcnow() + timedelta(days=self.srs_interval * 2)
        elif self.status == "failed":
            # More frequent reviews for failed words
            self.next_review_at = datetime.utcnow() + timedelta(hours=4)
        else:
            self.next_review_at = datetime.utcnow() + timedelta(days=self.srs_interval)
    
    def is_due_for_review(self) -> bool:
        """Check if the word is due for review."""
        return datetime.utcnow() >= self.next_review_at
    
    def days_until_review(self) -> int:
        """Get days until next review."""
        delta = self.next_review_at - datetime.utcnow()
        return max(0, delta.days)
    
    def to_dict(self) -> dict:
        """Convert progress to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "word_id": self.word_id,
            "status": self.status,
            "srs_level": self.srs_level,
            "srs_interval": self.srs_interval,
            "ease_factor": self.ease_factor,
            "total_reviews": self.total_reviews,
            "correct_reviews": self.correct_reviews,
            "accuracy_rate": self.accuracy_rate,
            "consecutive_correct": self.consecutive_correct,
            "consecutive_incorrect": self.consecutive_incorrect,
            "is_favorite": self.is_favorite,
            "is_flagged": self.is_flagged,
            "difficulty_rating": self.difficulty_rating,
            "next_review_at": self.next_review_at.isoformat() if self.next_review_at else None,
            "last_reviewed_at": self.last_reviewed_at.isoformat() if self.last_reviewed_at else None,
            "first_seen_at": self.first_seen_at.isoformat() if self.first_seen_at else None,
            "mastered_at": self.mastered_at.isoformat() if self.mastered_at else None,
        } 