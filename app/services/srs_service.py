"""SRS service for managing Spaced Repetition System and learning progress."""

import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.word import Word
from app.db.models.user_word_progress import UserWordProgress
from app.db.repositories.user_word_progress import UserWordProgressRepository
from app.services.word_management_service import WordManagementService

logger = logging.getLogger(__name__)


class SRSService:
    """Service for Spaced Repetition System and learning management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.progress_repo = UserWordProgressRepository(db)
        self.word_service = WordManagementService(db)
    
    async def assign_words_to_user(self, user: User, words: List[Word]) -> List[UserWordProgress]:
        """Assign new words to a user and create progress tracking."""
        progress_list = []
        
        for word in words:
            # Create or get existing progress
            progress = await self.progress_repo.create_or_get_progress(
                user_id=user.id,
                word_id=word.id
            )
            progress_list.append(progress)
        
        logger.info(f"Assigned {len(words)} words to user {user.id}")
        return progress_list
    
    async def record_word_review(
        self,
        user_id: int,
        word_id: int,
        is_correct: bool,
        response_time: Optional[float] = None,
        difficulty_rating: Optional[int] = None
    ) -> Optional[UserWordProgress]:
        """Record a word review and update SRS parameters."""
        progress = await self.progress_repo.get_by_user_and_word(user_id, word_id)
        
        if not progress:
            logger.warning(f"No progress found for user {user_id}, word {word_id}")
            return None
        
        # Record the review
        progress.record_review(
            is_correct=is_correct,
            response_time=response_time,
            difficulty=difficulty_rating
        )
        
        # Save changes
        await self.db.commit()
        
        logger.info(f"Recorded review for user {user_id}, word {word_id}: {'correct' if is_correct else 'incorrect'}")
        return progress
    
    async def get_words_due_for_review(self, user_id: int) -> List[UserWordProgress]:
        """Get words that are due for review."""
        return await self.progress_repo.get_words_due_for_review(user_id)
    
    async def get_user_progress_by_status(self, user_id: int, status: str) -> List[UserWordProgress]:
        """Get user's word progress by learning status."""
        return await self.progress_repo.get_user_progress_by_status(user_id, status)
    
    async def get_daily_learning_words(
        self,
        user: User,
        include_reviews: bool = True,
        include_new: bool = True
    ) -> dict:
        """
        Get words for daily learning session.
        Combines reviews due and new words based on user preferences.
        """
        result = {
            "review_words": [],
            "new_words": [],
            "total_count": 0
        }
        
        if include_reviews:
            # Get words due for review
            review_progress = await self.get_words_due_for_review(user.id)
            result["review_words"] = review_progress
        
        if include_new:
            # Calculate how many new words to include
            review_count = len(result["review_words"])
            remaining_slots = max(0, user.daily_word_count - review_count)
            
            if remaining_slots > 0:
                # Get words that user hasn't learned yet
                learned_word_ids = await self._get_user_learned_word_ids(user.id)
                
                new_words = await self.word_service.get_or_generate_words(
                    user=user,
                    word_count=remaining_slots,
                    exclude_word_ids=learned_word_ids
                )
                
                # Assign new words to user
                if new_words:
                    await self.assign_words_to_user(user, new_words)
                
                result["new_words"] = new_words
        
        result["total_count"] = len(result["review_words"]) + len(result["new_words"])
        
        logger.info(f"Daily learning session for user {user.id}: {len(result['review_words'])} reviews, {len(result['new_words'])} new")
        return result
    
    async def _get_user_learned_word_ids(self, user_id: int) -> List[int]:
        """Get IDs of words the user has already encountered."""
        all_progress = await self.progress_repo.get_by_filter(user_id=user_id)
        return [progress.word_id for progress in all_progress]
    
    async def get_user_learning_statistics(self, user_id: int) -> dict:
        """Get comprehensive learning statistics for a user."""
        all_progress = await self.progress_repo.get_by_filter(user_id=user_id)
        
        # Group by status
        status_counts = {}
        total_reviews = 0
        total_correct = 0
        
        for progress in all_progress:
            status = progress.status
            status_counts[status] = status_counts.get(status, 0) + 1
            total_reviews += progress.total_reviews
            total_correct += progress.correct_reviews
        
        # Calculate overall accuracy
        overall_accuracy = (total_correct / total_reviews) if total_reviews > 0 else 0.0
        
        # Get words due for review
        due_count = len(await self.get_words_due_for_review(user_id))
        
        return {
            "total_words": len(all_progress),
            "status_breakdown": status_counts,
            "total_reviews": total_reviews,
            "total_correct": total_correct,
            "overall_accuracy": overall_accuracy,
            "words_due_for_review": due_count,
            "new_words": status_counts.get("new", 0),
            "learning_words": status_counts.get("learning", 0),
            "mastered_words": status_counts.get("mastered", 0),
            "failed_words": status_counts.get("failed", 0)
        }
    
    async def flag_difficult_word(self, user_id: int, word_id: int, is_flagged: bool = True) -> Optional[UserWordProgress]:
        """Flag or unflag a word as difficult for a user."""
        progress = await self.progress_repo.get_by_user_and_word(user_id, word_id)
        if progress:
            return await self.progress_repo.update_by_id(
                progress.id,
                is_flagged=is_flagged
            )
        return None
    
    async def mark_word_as_favorite(self, user_id: int, word_id: int, is_favorite: bool = True) -> Optional[UserWordProgress]:
        """Mark or unmark a word as favorite for a user."""
        progress = await self.progress_repo.get_by_user_and_word(user_id, word_id)
        if progress:
            return await self.progress_repo.update_by_id(
                progress.id,
                is_favorite=is_favorite
            )
        return None
    
    async def add_user_note_to_word(self, user_id: int, word_id: int, note: str) -> Optional[UserWordProgress]:
        """Add a personal note to a word for a user."""
        progress = await self.progress_repo.get_by_user_and_word(user_id, word_id)
        if progress:
            return await self.progress_repo.update_by_id(
                progress.id,
                notes=note
            )
        return None
    
    async def reset_word_progress(self, user_id: int, word_id: int) -> Optional[UserWordProgress]:
        """Reset the learning progress for a specific word."""
        progress = await self.progress_repo.get_by_user_and_word(user_id, word_id)
        if progress:
            # Reset to initial state
            return await self.progress_repo.update_by_id(
                progress.id,
                status="new",
                srs_level=0,
                srs_interval=1,
                ease_factor=2.5,
                consecutive_correct=0,
                consecutive_incorrect=0,
                next_review_at=datetime.utcnow()
            )
        return None 