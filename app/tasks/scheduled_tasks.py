"""Scheduled Celery tasks for daily vocabulary and maintenance."""

import logging
from datetime import datetime, timedelta
from typing import List

from app.tasks.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.db.repositories.user import UserRepository
from app.services.word_management_service import WordManagementService
from app.services.srs_service import SRSService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def send_daily_vocabulary_to_all_users(self):
    """Send daily vocabulary to all active users."""
    import asyncio
    return asyncio.run(_send_daily_vocabulary_async())


async def _send_daily_vocabulary_async():
    """Async implementation of daily vocabulary sending."""
    async with AsyncSessionLocal() as db:
        user_repo = UserRepository(db)
        word_service = WordManagementService(db)
        srs_service = SRSService(db)
        
        # Get all active users who should receive daily words
        users = await user_repo.get_by_filter(
            is_active=True,
            notifications_enabled=True
        )
        
        success_count = 0
        error_count = 0
        
        for user in users:
            try:
                # Check if user already received words today
                if _should_send_daily_words(user):
                    # Get daily learning session
                    learning_session = await srs_service.get_daily_learning_words(
                        user=user,
                        include_reviews=True,
                        include_new=True
                    )
                    
                    if learning_session["total_count"] > 0:
                        # Send words via Telegram (this would integrate with bot)
                        await _send_telegram_vocabulary(user, learning_session)
                        
                        # Update user's last daily words sent timestamp
                        await user_repo.update_by_id(
                            user.id,
                            last_daily_words_sent=datetime.utcnow()
                        )
                        
                        success_count += 1
                        logger.info(f"Sent daily vocabulary to user {user.id}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to send daily vocabulary to user {user.id}: {e}")
        
        logger.info(f"Daily vocabulary task completed: {success_count} success, {error_count} errors")
        return {"success": success_count, "errors": error_count}


def _should_send_daily_words(user) -> bool:
    """Check if user should receive daily words."""
    if not user.last_daily_words_sent:
        return True
    
    # Check if it's been more than 20 hours since last send
    time_diff = datetime.utcnow() - user.last_daily_words_sent
    return time_diff.total_seconds() > 20 * 3600  # 20 hours


async def _send_telegram_vocabulary(user, learning_session):
    """Send vocabulary to user via Telegram (placeholder)."""
    # This would integrate with the Telegram bot to send messages
    # For now, it's just a placeholder
    logger.info(f"Would send {learning_session['total_count']} words to user {user.telegram_id}")


@celery_app.task(bind=True)
def cleanup_old_data(self):
    """Clean up old data and perform maintenance tasks."""
    import asyncio
    return asyncio.run(_cleanup_old_data_async())


async def _cleanup_old_data_async():
    """Async implementation of data cleanup."""
    async with AsyncSessionLocal() as db:
        cleanup_tasks = []
        
        # Clean up old unverified words (older than 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # This is a placeholder for actual cleanup logic
        logger.info(f"Running cleanup for data older than {cutoff_date}")
        
        # Add more cleanup tasks as needed:
        # - Remove old logs
        # - Clean up unused LLM responses
        # - Archive old user sessions
        # - Update usage statistics
        
        return {"cleanup_date": cutoff_date.isoformat(), "tasks_completed": len(cleanup_tasks)}


@celery_app.task(bind=True)
def generate_vocabulary_cache(self, difficulty_level: str, word_count: int = 100):
    """Pre-generate vocabulary cache for better performance."""
    import asyncio
    return asyncio.run(_generate_vocabulary_cache_async(difficulty_level, word_count))


async def _generate_vocabulary_cache_async(difficulty_level: str, word_count: int):
    """Async implementation of vocabulary cache generation."""
    async with AsyncSessionLocal() as db:
        word_service = WordManagementService(db)
        
        try:
            # Create a dummy user profile for generation
            user_profile = {
                "difficulty_level": difficulty_level,
                "total_words_learned": 0,
                "language_code": "tr"
            }
            
            # Generate vocabulary
            vocabulary_data = await word_service.llm_service.generate_vocabulary_set(
                user_profile=user_profile,
                word_count=word_count,
                difficulty_reference=f"Oxford3000_{difficulty_level}"
            )
            
            # Cache the words
            cached_count = 0
            for word_data in vocabulary_data:
                try:
                    # Check if word already exists
                    existing_word = await word_service.word_repo.get_word_by_text_if_verified(
                        word_data["english_word"]
                    )
                    
                    if not existing_word:
                        await word_service._cache_word_with_examples(word_data)
                        cached_count += 1
                
                except Exception as e:
                    logger.error(f"Failed to cache word {word_data.get('english_word')}: {e}")
            
            logger.info(f"Cached {cached_count} new words for difficulty {difficulty_level}")
            return {"difficulty_level": difficulty_level, "cached_count": cached_count}
            
        except Exception as e:
            logger.error(f"Failed to generate vocabulary cache: {e}")
            return {"error": str(e)}


@celery_app.task(bind=True)
def update_user_streaks(self):
    """Update learning streaks for all users."""
    import asyncio
    return asyncio.run(_update_user_streaks_async())


async def _update_user_streaks_async():
    """Async implementation of streak updates."""
    async with AsyncSessionLocal() as db:
        user_repo = UserRepository(db)
        
        # Get all active users
        users = await user_repo.get_by_filter(is_active=True)
        
        updated_count = 0
        
        for user in users:
            try:
                # Check if user has activity in the last 24 hours
                if user.last_activity:
                    time_since_activity = datetime.utcnow() - user.last_activity
                    
                    if time_since_activity.total_seconds() > 48 * 3600:  # 48 hours
                        # Reset streak if no activity for 48 hours
                        if user.learning_streak > 0:
                            await user_repo.update_by_id(user.id, learning_streak=0)
                            updated_count += 1
                            logger.info(f"Reset streak for inactive user {user.id}")
                
            except Exception as e:
                logger.error(f"Failed to update streak for user {user.id}: {e}")
        
        logger.info(f"Updated streaks for {updated_count} users")
        return {"updated_count": updated_count}


@celery_app.task(bind=True) 
def verify_word_quality(self, word_id: int):
    """Verify the quality of a specific word using LLM."""
    import asyncio
    return asyncio.run(_verify_word_quality_async(word_id))


async def _verify_word_quality_async(word_id: int):
    """Async implementation of word quality verification."""
    async with AsyncSessionLocal() as db:
        word_service = WordManagementService(db)
        
        try:
            quality_score = await word_service.verify_word_quality(word_id)
            
            if quality_score is not None:
                logger.info(f"Verified word {word_id} with quality score {quality_score}")
                return {"word_id": word_id, "quality_score": quality_score}
            else:
                logger.warning(f"Failed to verify word {word_id}")
                return {"word_id": word_id, "error": "Verification failed"}
                
        except Exception as e:
            logger.error(f"Error verifying word {word_id}: {e}")
            return {"word_id": word_id, "error": str(e)} 