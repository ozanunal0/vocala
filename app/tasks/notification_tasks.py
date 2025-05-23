"""Notification tasks for sending messages to users."""

import logging
from typing import List, Dict, Any

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def send_telegram_message(self, telegram_id: int, message: str, parse_mode: str = None):
    """Send a message to a specific Telegram user."""
    try:
        # This would integrate with the Telegram bot API
        # For now, it's a placeholder
        logger.info(f"Sending message to {telegram_id}: {message[:50]}...")
        
        # In a real implementation, this would:
        # 1. Get the bot instance
        # 2. Send the message via bot.send_message()
        # 3. Handle any errors (user blocked bot, invalid chat_id, etc.)
        
        return {"success": True, "telegram_id": telegram_id}
        
    except Exception as e:
        logger.error(f"Failed to send message to {telegram_id}: {e}")
        return {"success": False, "telegram_id": telegram_id, "error": str(e)}


@celery_app.task(bind=True)
def send_bulk_notifications(self, notifications: List[Dict[str, Any]]):
    """Send notifications to multiple users."""
    results = []
    
    for notification in notifications:
        try:
            telegram_id = notification["telegram_id"]
            message = notification["message"]
            parse_mode = notification.get("parse_mode")
            
            # Send individual message
            result = send_telegram_message.delay(telegram_id, message, parse_mode)
            results.append({"telegram_id": telegram_id, "task_id": result.id})
            
        except Exception as e:
            logger.error(f"Failed to queue notification: {e}")
            results.append({"telegram_id": notification.get("telegram_id"), "error": str(e)})
    
    return {"queued": len(results), "results": results}


@celery_app.task(bind=True)
def send_learning_reminder(self, telegram_id: int, user_name: str):
    """Send a learning reminder to a user."""
    message = f"""
🔔 Daily Learning Reminder

Hi {user_name}! 

Don't forget to practice your vocabulary today. Use /daily to get your words and maintain your learning streak! 🔥

Keep up the great work! 📚✨
    """
    
    return send_telegram_message.delay(telegram_id, message.strip())


@celery_app.task(bind=True)
def send_streak_milestone(self, telegram_id: int, user_name: str, streak_days: int):
    """Send a streak milestone notification."""
    milestone_messages = {
        7: "🎉 Amazing! You've reached a 7-day streak!",
        30: "🔥 Incredible! 30 days of consistent learning!",
        100: "🏆 Outstanding! 100 days of vocabulary mastery!",
        365: "👑 Legendary! One full year of learning!"
    }
    
    milestone_message = milestone_messages.get(
        streak_days, 
        f"🎯 Great job! {streak_days} days of consistent learning!"
    )
    
    message = f"""
{milestone_message}

Hi {user_name}! 

Your dedication to learning English vocabulary is truly inspiring. Keep going! 

Stats: {streak_days} days streak 🔥
Use /progress to see your full statistics.
    """
    
    return send_telegram_message.delay(telegram_id, message.strip())


@celery_app.task(bind=True)
def send_word_mastery_notification(self, telegram_id: int, user_name: str, word: str, total_mastered: int):
    """Send notification when user masters a word."""
    message = f"""
🌟 Word Mastered!

Congratulations {user_name}! 

You've successfully mastered the word: **{word}**

Total mastered words: {total_mastered} 📚

Keep up the excellent work! Each word brings you closer to fluency.
    """
    
    return send_telegram_message.delay(telegram_id, message.strip(), "Markdown")


@celery_app.task(bind=True)
def send_review_reminder(self, telegram_id: int, user_name: str, review_count: int):
    """Send reminder about pending reviews."""
    message = f"""
📝 Review Time!

Hi {user_name}! 

You have {review_count} word(s) ready for review. Regular reviews help strengthen your memory and improve retention.

Use /daily to start your review session! 

🧠 Spaced repetition = Better learning 🎯
    """
    
    return send_telegram_message.delay(telegram_id, message.strip())


@celery_app.task(bind=True)
def send_weekly_progress_report(self, telegram_id: int, user_name: str, stats: Dict[str, Any]):
    """Send weekly progress report to user."""
    message = f"""
📊 Weekly Progress Report

Hi {user_name}! Here's your learning summary:

📚 New words learned: {stats.get('new_words', 0)}
✅ Total reviews completed: {stats.get('reviews_completed', 0)}
🎯 Accuracy rate: {stats.get('accuracy_rate', 0):.1%}
🔥 Current streak: {stats.get('streak_days', 0)} days
⭐ Mastered words: {stats.get('mastered_words', 0)}

{_get_motivation_message(stats)}

Keep up the fantastic work! 🌟
    """
    
    return send_telegram_message.delay(telegram_id, message.strip())


def _get_motivation_message(stats: Dict[str, Any]) -> str:
    """Get a motivational message based on user stats."""
    accuracy = stats.get('accuracy_rate', 0)
    streak = stats.get('streak_days', 0)
    
    if accuracy >= 0.9:
        return "🏆 Excellent accuracy! You're really mastering these words!"
    elif accuracy >= 0.7:
        return "👍 Good progress! Keep practicing to improve further!"
    elif streak >= 7:
        return "🔥 Great consistency! Your daily practice is paying off!"
    else:
        return "💪 Every step counts! Keep going, you're doing great!"


@celery_app.task(bind=True)
def send_system_notification(self, telegram_id: int, title: str, message: str, priority: str = "normal"):
    """Send system notifications (updates, maintenance, etc.)."""
    priority_icons = {
        "low": "ℹ️",
        "normal": "📢", 
        "high": "⚠️",
        "urgent": "🚨"
    }
    
    icon = priority_icons.get(priority, "📢")
    
    formatted_message = f"""
{icon} {title}

{message}

- Vocala Team
    """
    
    return send_telegram_message.delay(telegram_id, formatted_message.strip()) 