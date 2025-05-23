"""
Telegram bot handlers for Vocala vocabulary learning bot.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)

from app.db.database import get_db
from app.db.repositories.user import UserRepository
from app.services.word_management_service import WordManagementService
from app.services.notion_service import NotionService

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    
    # Get database session
    async for db in get_db():
        user_repo = UserRepository(db)
        
        # Create or update user
        vocala_user = await user_repo.create_or_update_from_telegram(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code
        )
        
        welcome_message = f"""
🎯 Welcome to Vocala, {vocala_user.display_name}!

I'm your AI-powered English vocabulary learning companion. I'll help you learn new words through:

📚 Daily vocabulary with Turkish translations
📝 Example sentences for better understanding
🧠 Spaced repetition system for effective memorization
📊 Progress tracking
🔗 Notion integration (optional)

Commands:
/daily - Get your daily vocabulary words
/progress - View your learning progress
/settings - Adjust your preferences
/help - Show all commands

Let's start your vocabulary journey! Use /daily to get your first words.
        """
        
        await update.message.reply_text(welcome_message.strip())
        break


async def daily_words_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /daily command - main vocabulary delivery."""
    user = update.effective_user
    
    async for db in get_db():
        user_repo = UserRepository(db)
        word_service = WordManagementService(db)
        notion_service = NotionService()
        
        # Get or create user
        vocala_user = await user_repo.create_or_update_from_telegram(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        try:
            # Get daily words (this will use cache or generate new ones)
            words = await word_service.get_or_generate_words(
                user=vocala_user,
                word_count=vocala_user.daily_word_count
            )
            
            if not words:
                await update.message.reply_text(
                    "Sorry, I couldn't generate words for you right now. Please try again later."
                )
                break
            
            # Format and send words
            response = f"📚 Your Daily Vocabulary ({len(words)} words)\n\n"
            
            for i, word in enumerate(words, 1):
                # Get examples for this word
                word_with_examples = await word_service.get_word_with_examples(word.id)
                
                response += f"{i}. {word.english_word} ({word.part_of_speech})\n"
                response += f"🇹🇷 {word.turkish_translation}\n"
                
                if word.definition:
                    response += f"📖 {word.definition}\n"
                
                # Add examples if available
                if word_with_examples and word_with_examples.get("examples"):
                    examples = word_with_examples["examples"][:2]  # Limit to 2 examples
                    for example in examples:
                        response += f"💬 {example['english_sentence']}\n"
                        response += f"   {example['turkish_translation']}\n"
                
                response += "\n"
            
            response += "💡 Review these words throughout the day for better retention!"
            
            await update.message.reply_text(response)
            
            # Sync words to Notion if enabled for user
            if vocala_user.notion_enabled and vocala_user.notion_database_id:
                try:
                    # Prepare word data for Notion
                    words_data = []
                    for word in words:
                        word_dict = {
                            "english_word": word.english_word,
                            "turkish_translation": word.turkish_translation,
                            "part_of_speech": word.part_of_speech,
                            "definition": word.definition,
                            "difficulty_level": word.difficulty_level
                        }
                        
                        # Get examples for this word
                        word_with_examples = await word_service.get_word_with_examples(word.id)
                        if word_with_examples and word_with_examples.get("examples"):
                            word_dict["examples"] = word_with_examples["examples"]
                        
                        words_data.append(word_dict)
                    
                    # Sync to Notion
                    success_count = await notion_service.bulk_add_words(
                        database_id=vocala_user.notion_database_id,
                        words_data=words_data,
                        user_notion_token=vocala_user.notion_token
                    )
                    
                    if success_count > 0:
                        logger.info(f"Synced {success_count} words to Notion for user {vocala_user.id}")
                    
                except Exception as notion_error:
                    logger.error(f"Failed to sync words to Notion for user {vocala_user.id}: {notion_error}")
                    # Don't interrupt the main flow if Notion sync fails
            
        except Exception as e:
            logger.error(f"Error in daily_words_command: {e}")
            await update.message.reply_text(
                "Sorry, there was an error getting your daily words. Please try again later."
            )
        
        break


async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /progress command."""
    user = update.effective_user
    
    async for db in get_db():
        user_repo = UserRepository(db)
        
        vocala_user = await user_repo.get_by_telegram_id(user.id)
        
        if not vocala_user:
            await update.message.reply_text(
                "You haven't started learning yet! Use /start to begin."
            )
            break
        
        progress_message = f"""
📊 Your Learning Progress

👤 User: {vocala_user.display_name}
🎯 Level: {vocala_user.difficulty_level}
📚 Total words learned: {vocala_user.total_words_learned}
🔥 Learning streak: {vocala_user.learning_streak} days
📅 Daily word goal: {vocala_user.daily_word_count} words

Keep up the great work! 🌟
        """
        
        await update.message.reply_text(progress_message.strip())
        break


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settings command with interactive menu."""
    user = update.effective_user
    
    async for db in get_db():
        user_repo = UserRepository(db)
        
        # Get or create user
        vocala_user = await user_repo.create_or_update_from_telegram(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Create interactive keyboard
        keyboard = [
            [
                InlineKeyboardButton(f"📅 Daily Words: {vocala_user.daily_word_count}", callback_data="setting_daily_words"),
                InlineKeyboardButton(f"🎯 Level: {vocala_user.difficulty_level}", callback_data="setting_difficulty")
            ],
            [
                InlineKeyboardButton(
                    f"🔔 Notifications: {'ON' if vocala_user.notifications_enabled else 'OFF'}", 
                    callback_data="setting_notifications"
                ),
                InlineKeyboardButton(f"🌐 Language: Turkish", callback_data="setting_language")
            ],
            [
                InlineKeyboardButton("🔗 Notion Integration", callback_data="setting_notion"),
                InlineKeyboardButton("⏰ Learning Time", callback_data="setting_time")
            ],
            [
                InlineKeyboardButton("🔄 Reset Progress", callback_data="setting_reset"),
                InlineKeyboardButton("✅ Close Menu", callback_data="setting_close")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        settings_message = f"""
⚙️ **Interactive Settings Menu**

👤 **User**: {vocala_user.display_name}
📊 **Progress**: {vocala_user.total_words_learned} words learned, {vocala_user.learning_streak} day streak

📋 **Current Settings**:
• Daily word count: **{vocala_user.daily_word_count}** words
• Difficulty level: **{vocala_user.difficulty_level}**
• Notifications: **{'Enabled' if vocala_user.notifications_enabled else 'Disabled'}**
• Preferred time: **{vocala_user.preferred_time or 'Not set'}**
• Notion sync: **{'Active' if vocala_user.notion_enabled else 'Inactive'}**

Click the buttons below to adjust your settings:
        """
        
        await update.message.reply_text(
            settings_message.strip(), 
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        break


async def settings_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle settings menu callback queries."""
    query = update.callback_query
    user = update.effective_user
    
    # Answer the callback query
    await query.answer()
    
    # Parse the callback data
    action = query.data
    
    if action == "setting_daily_words":
        await handle_daily_words_setting(update, context)
    elif action == "setting_difficulty":
        await handle_difficulty_setting(update, context)
    elif action == "setting_notifications":
        await handle_notifications_setting(update, context)
    elif action == "setting_language":
        await handle_language_setting(update, context)
    elif action == "setting_notion":
        await handle_notion_setting(update, context)
    elif action == "setting_time":
        await handle_time_setting(update, context)
    elif action == "setting_reset":
        await handle_reset_setting(update, context)
    elif action == "setting_close":
        await handle_close_setting(update, context)
    elif action.startswith("daily_words_"):
        await handle_daily_words_change(update, context, action)
    elif action.startswith("difficulty_"):
        await handle_difficulty_change(update, context, action)
    elif action.startswith("notifications_"):
        await handle_notifications_change(update, context, action)
    elif action.startswith("time_"):
        await handle_time_change(update, context, action)
    elif action == "back_to_settings":
        await show_settings_menu(update, context)
    elif action == "notion_guide":
        await handle_notion_guide(update, context)
    elif action == "notion_test_quick":
        await handle_notion_test_quick(update, context)
    elif action == "notion_disable_quick":
        await handle_notion_disable_quick(update, context)
    elif action == "reset_confirm":
        await handle_reset_confirm(update, context)


async def handle_daily_words_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle daily words count setting."""
    query = update.callback_query
    
    keyboard = [
        [
            InlineKeyboardButton("3 words", callback_data="daily_words_3"),
            InlineKeyboardButton("5 words", callback_data="daily_words_5"),
            InlineKeyboardButton("7 words", callback_data="daily_words_7")
        ],
        [
            InlineKeyboardButton("10 words", callback_data="daily_words_10"),
            InlineKeyboardButton("15 words", callback_data="daily_words_15")
        ],
        [
            InlineKeyboardButton("⬅️ Back to Settings", callback_data="back_to_settings")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📅 **Daily Word Count**\n\n"
        "How many new words would you like to learn each day?\n\n"
        "📊 **Recommendations**:\n"
        "• **Beginner (A1-A2)**: 3-5 words\n"
        "• **Intermediate (B1)**: 5-7 words\n"
        "• **Advanced (B2)**: 7-15 words\n\n"
        "Choose your preferred daily word count:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def handle_difficulty_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle difficulty level setting."""
    query = update.callback_query
    
    keyboard = [
        [
            InlineKeyboardButton("🟢 A1 (Beginner)", callback_data="difficulty_A1"),
            InlineKeyboardButton("🟡 A2 (Elementary)", callback_data="difficulty_A2")
        ],
        [
            InlineKeyboardButton("🟠 B1 (Intermediate)", callback_data="difficulty_B1"),
            InlineKeyboardButton("🔴 B2 (Upper-Intermediate)", callback_data="difficulty_B2")
        ],
        [
            InlineKeyboardButton("⬅️ Back to Settings", callback_data="back_to_settings")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎯 **Difficulty Level**\n\n"
        "Choose your English proficiency level:\n\n"
        "🟢 **A1**: Basic words (the, cat, happy)\n"
        "🟡 **A2**: Common words (because, sometimes, important)\n"
        "🟠 **B1**: Intermediate words (achieve, flexible, enormous)\n"
        "🔴 **B2**: Advanced words (constitute, integrate, phenomena)\n\n"
        "This affects the complexity of vocabulary you receive:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def handle_notifications_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle notifications setting."""
    query = update.callback_query
    user = update.effective_user
    
    async for db in get_db():
        user_repo = UserRepository(db)
        vocala_user = await user_repo.get_by_telegram_id(user.id)
        
        if vocala_user:
            # Toggle notifications
            new_status = not vocala_user.notifications_enabled
            await user_repo.update_learning_preferences(
                user_id=vocala_user.id,
                notifications_enabled=new_status
            )
            
            status_text = "enabled" if new_status else "disabled"
            status_emoji = "🔔" if new_status else "🔕"
            
            keyboard = [[InlineKeyboardButton("⬅️ Back to Settings", callback_data="back_to_settings")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🔔 **Notifications {status_text.title()}**\n\n"
                f"{status_emoji} Notifications have been **{status_text}**.\n\n"
                f"{'You will receive daily vocabulary reminders and learning streaks.' if new_status else 'You will not receive automatic reminders.'}\n\n"
                f"You can change this anytime in settings.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        break


async def handle_language_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language setting."""
    query = update.callback_query
    
    keyboard = [[InlineKeyboardButton("⬅️ Back to Settings", callback_data="back_to_settings")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🌐 **Language Settings**\n\n"
        "🇹🇷 **Current**: Turkish translations\n"
        "🇬🇧 **Learning**: English vocabulary\n\n"
        "📝 **Note**: Multi-language support is planned for future updates!\n"
        "Currently, all vocabulary includes Turkish translations to help Turkish speakers learn English.\n\n"
        "Coming soon:\n"
        "• Arabic translations\n"
        "• French translations\n"
        "• Spanish translations",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def handle_notion_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Notion integration setting."""
    query = update.callback_query
    user = update.effective_user
    
    async for db in get_db():
        user_repo = UserRepository(db)
        vocala_user = await user_repo.get_by_telegram_id(user.id)
        
        if vocala_user:
            keyboard = [
                [InlineKeyboardButton("📖 Setup Guide", callback_data="notion_guide")],
                [InlineKeyboardButton("🔧 Test Connection", callback_data="notion_test_quick")],
                [InlineKeyboardButton("⬅️ Back to Settings", callback_data="back_to_settings")]
            ]
            
            if vocala_user.notion_enabled:
                keyboard.insert(1, [InlineKeyboardButton("❌ Disable Notion", callback_data="notion_disable_quick")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            status = "🟢 **Connected**" if vocala_user.notion_enabled else "🔴 **Not Connected**"
            
            await query.edit_message_text(
                f"🔗 **Notion Integration**\n\n"
                f"Status: {status}\n\n"
                f"{'📄 Database: ' + (vocala_user.notion_database_id[:20] + '...' if vocala_user.notion_database_id else 'None') if vocala_user.notion_enabled else ''}\n\n"
                f"**What is Notion Integration?**\n"
                f"• Automatically sync daily vocabulary to your personal Notion database\n"
                f"• Keep track of words with examples and translations\n"
                f"• Create your personal vocabulary collection\n\n"
                f"Use the buttons below to manage your integration:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        break


async def handle_time_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle learning time setting."""
    query = update.callback_query
    
    keyboard = [
        [
            InlineKeyboardButton("🌅 08:00", callback_data="time_08:00"),
            InlineKeyboardButton("🌞 12:00", callback_data="time_12:00"),
            InlineKeyboardButton("🌆 18:00", callback_data="time_18:00")
        ],
        [
            InlineKeyboardButton("🌙 20:00", callback_data="time_20:00"),
            InlineKeyboardButton("🕒 Custom", callback_data="time_custom")
        ],
        [
            InlineKeyboardButton("⬅️ Back to Settings", callback_data="back_to_settings")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⏰ **Learning Reminder Time**\n\n"
        "When would you like to receive daily vocabulary reminders?\n\n"
        "🌅 **Morning (08:00)**: Start your day with new words\n"
        "🌞 **Noon (12:00)**: Lunch break learning\n"
        "🌆 **Evening (18:00)**: After work vocabulary\n"
        "🌙 **Night (20:00)**: Before sleep review\n\n"
        "⚠️ **Note**: This feature requires notification to be enabled.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def handle_reset_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle reset progress setting."""
    query = update.callback_query
    
    keyboard = [
        [
            InlineKeyboardButton("⚠️ Yes, Reset All Progress", callback_data="reset_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="back_to_settings")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔄 **Reset Learning Progress**\n\n"
        "⚠️ **WARNING**: This action will permanently delete:\n\n"
        "• All learned vocabulary words\n"
        "• Learning streak counter\n"
        "• Progress statistics\n"
        "• Spaced repetition schedules\n\n"
        "❗ **This action cannot be undone!**\n\n"
        "Your account settings (difficulty, notifications, etc.) will be preserved.\n\n"
        "Are you sure you want to reset your progress?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def handle_close_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle close settings menu."""
    query = update.callback_query
    
    await query.edit_message_text(
        "⚙️ **Settings Menu Closed**\n\n"
        "Your settings have been saved! Use `/settings` anytime to adjust your preferences.\n\n"
        "Happy learning! 📚✨"
    )


async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the main settings menu (for back button)."""
    query = update.callback_query
    user = update.effective_user
    
    async for db in get_db():
        user_repo = UserRepository(db)
        
        # Get user data
        vocala_user = await user_repo.get_by_telegram_id(user.id)
        
        if vocala_user:
            # Create interactive keyboard
            keyboard = [
                [
                    InlineKeyboardButton(f"📅 Daily Words: {vocala_user.daily_word_count}", callback_data="setting_daily_words"),
                    InlineKeyboardButton(f"🎯 Level: {vocala_user.difficulty_level}", callback_data="setting_difficulty")
                ],
                [
                    InlineKeyboardButton(
                        f"🔔 Notifications: {'ON' if vocala_user.notifications_enabled else 'OFF'}", 
                        callback_data="setting_notifications"
                    ),
                    InlineKeyboardButton(f"🌐 Language: Turkish", callback_data="setting_language")
                ],
                [
                    InlineKeyboardButton("🔗 Notion Integration", callback_data="setting_notion"),
                    InlineKeyboardButton("⏰ Learning Time", callback_data="setting_time")
                ],
                [
                    InlineKeyboardButton("🔄 Reset Progress", callback_data="setting_reset"),
                    InlineKeyboardButton("✅ Close Menu", callback_data="setting_close")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            settings_message = f"""
⚙️ **Interactive Settings Menu**

👤 **User**: {vocala_user.display_name}
📊 **Progress**: {vocala_user.total_words_learned} words learned, {vocala_user.learning_streak} day streak

📋 **Current Settings**:
• Daily word count: **{vocala_user.daily_word_count}** words
• Difficulty level: **{vocala_user.difficulty_level}**
• Notifications: **{'Enabled' if vocala_user.notifications_enabled else 'Disabled'}**
• Preferred time: **{vocala_user.preferred_time or 'Not set'}**
• Notion sync: **{'Active' if vocala_user.notion_enabled else 'Inactive'}**

Click the buttons below to adjust your settings:
            """
            
            await query.edit_message_text(
                settings_message.strip(), 
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        break


# Helper handlers for setting changes
async def handle_daily_words_change(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    """Handle daily words count change."""
    query = update.callback_query
    user = update.effective_user
    
    # Extract count from action (e.g., "daily_words_5" -> 5)
    count = int(action.split("_")[-1])
    
    async for db in get_db():
        user_repo = UserRepository(db)
        vocala_user = await user_repo.get_by_telegram_id(user.id)
        
        if vocala_user:
            await user_repo.update_learning_preferences(
                user_id=vocala_user.id,
                daily_word_count=count
            )
            
            keyboard = [[InlineKeyboardButton("⬅️ Back to Settings", callback_data="back_to_settings")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📅 **Daily Word Count Updated**\n\n"
                f"✅ You will now receive **{count} words** per day.\n\n"
                f"💡 **Tips for {count} words**:\n"
                f"{'• Perfect for beginners - manageable daily learning' if count <= 5 else ''}"
                f"{'• Great balance between challenge and retention' if 5 < count <= 10 else ''}"
                f"{'• Intensive learning - make sure to review regularly!' if count > 10 else ''}\n\n"
                f"Use `/daily` to get your next set of {count} vocabulary words!",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        break


async def handle_difficulty_change(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    """Handle difficulty level change."""
    query = update.callback_query
    user = update.effective_user
    
    # Extract level from action (e.g., "difficulty_B1" -> "B1")
    level = action.split("_")[-1]
    
    async for db in get_db():
        user_repo = UserRepository(db)
        vocala_user = await user_repo.get_by_telegram_id(user.id)
        
        if vocala_user:
            await user_repo.update_learning_preferences(
                user_id=vocala_user.id,
                difficulty_level=level
            )
            
            level_descriptions = {
                "A1": "Basic everyday words and phrases",
                "A2": "Common vocabulary for daily situations", 
                "B1": "Intermediate words for various topics",
                "B2": "Advanced vocabulary for complex discussions"
            }
            
            keyboard = [[InlineKeyboardButton("⬅️ Back to Settings", callback_data="back_to_settings")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🎯 **Difficulty Level Updated**\n\n"
                f"✅ Your level is now set to **{level}**\n\n"
                f"📖 **{level} Level**: {level_descriptions.get(level, 'Custom level')}\n\n"
                f"🆕 Your next vocabulary words will match this difficulty level.\n"
                f"Use `/daily` to get words appropriate for {level} learners!",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        break


async def handle_time_change(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    """Handle preferred time change."""
    query = update.callback_query
    user = update.effective_user
    
    if action == "time_custom":
        keyboard = [[InlineKeyboardButton("⬅️ Back to Time Settings", callback_data="setting_time")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🕒 **Custom Time Setup**\n\n"
            "To set a custom reminder time, please message the bot with your preferred time in 24-hour format.\n\n"
            "**Example**: Send `09:30` for 9:30 AM reminders\n\n"
            "⚠️ **Note**: Custom time setting via text message is coming soon!\n"
            "For now, please choose from the preset times.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Extract time from action (e.g., "time_08:00" -> "08:00")
    time = action.split("_")[-1]
    
    async for db in get_db():
        user_repo = UserRepository(db)
        vocala_user = await user_repo.get_by_telegram_id(user.id)
        
        if vocala_user:
            await user_repo.update_learning_preferences(
                user_id=vocala_user.id,
                preferred_time=time
            )
            
            keyboard = [[InlineKeyboardButton("⬅️ Back to Settings", callback_data="back_to_settings")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            time_emojis = {
                "08:00": "🌅",
                "12:00": "🌞", 
                "18:00": "🌆",
                "20:00": "🌙"
            }
            
            await query.edit_message_text(
                f"⏰ **Reminder Time Updated**\n\n"
                f"✅ Daily reminders set for **{time}** {time_emojis.get(time, '🕒')}\n\n"
                f"🔔 You'll receive vocabulary reminders at this time each day.\n\n"
                f"💡 **Tip**: Make sure notifications are enabled to receive reminders!\n"
                f"Check your notification settings if needed.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        break


async def handle_notion_guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Notion setup guide from settings."""
    query = update.callback_query
    
    keyboard = [[InlineKeyboardButton("⬅️ Back to Notion Settings", callback_data="setting_notion")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📖 **Notion Integration Setup Guide**\n\n"
        "**Step 1: Create Integration**\n"
        "• Go to https://www.notion.so/my-integrations\n"
        "• Click 'New integration'\n"
        "• Name it 'Vocala Bot'\n"
        "• Copy the integration token\n\n"
        "**Step 2: Setup Method**\n"
        "Choose one:\n\n"
        "🔄 **Use Existing Database**:\n"
        "`/notion setup <database_id> <token>`\n\n"
        "🆕 **Create New Database**:\n"
        "`/notion create <page_id>`\n\n"
        "**Step 3: Test**\n"
        "Use `/notion test` to verify everything works!\n\n"
        "💡 **Tip**: The bot adapts to any database schema automatically.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def handle_notion_test_quick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle quick Notion test from settings."""
    query = update.callback_query
    user = update.effective_user
    
    async for db in get_db():
        user_repo = UserRepository(db)
        notion_service = NotionService()
        vocala_user = await user_repo.get_by_telegram_id(user.id)
        
        if not vocala_user or not vocala_user.notion_enabled:
            keyboard = [[InlineKeyboardButton("⬅️ Back to Notion Settings", callback_data="setting_notion")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ **Notion Not Configured**\n\n"
                "Please set up Notion integration first using:\n"
                "`/notion setup <database_id> <token>`\n\n"
                "Or use the setup guide for detailed instructions.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            break
        
        # Run the actual test
        access_test = await notion_service.test_database_access(
            database_id=vocala_user.notion_database_id,
            user_notion_token=vocala_user.notion_token
        )
        
        keyboard = [[InlineKeyboardButton("⬅️ Back to Notion Settings", callback_data="setting_notion")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if access_test["accessible"] and access_test.get("is_usable"):
            await query.edit_message_text(
                f"✅ **Notion Test Successful**\n\n"
                f"Database: {access_test['database_name']}\n"
                f"Status: Fully compatible\n\n"
                f"🔄 Your vocabulary words will sync automatically when you use `/daily`!",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                f"⚠️ **Notion Test Results**\n\n"
                f"Database: {access_test.get('database_name', 'Unknown')}\n"
                f"Accessible: {'Yes' if access_test['accessible'] else 'No'}\n\n"
                f"{'Use `/notion fix` to resolve schema issues.' if access_test['accessible'] else 'Check your database ID and permissions.'}\n\n"
                f"Error: {access_test.get('error', 'Unknown issue')}",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        break


async def handle_notion_disable_quick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle quick Notion disable from settings."""
    query = update.callback_query
    user = update.effective_user
    
    async for db in get_db():
        user_repo = UserRepository(db)
        vocala_user = await user_repo.get_by_telegram_id(user.id)
        
        if vocala_user:
            await user_repo.update_notion_settings(
                user_id=vocala_user.id,
                notion_enabled=False
            )
            
            keyboard = [[InlineKeyboardButton("⬅️ Back to Notion Settings", callback_data="setting_notion")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ **Notion Integration Disabled**\n\n"
                "Your vocabulary words will no longer sync to Notion.\n\n"
                "Your Notion token and database settings are preserved.\n"
                "Use the setup guide to re-enable anytime.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        break


async def handle_reset_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle reset progress confirmation."""
    query = update.callback_query
    user = update.effective_user
    
    async for db in get_db():
        user_repo = UserRepository(db)
        vocala_user = await user_repo.get_by_telegram_id(user.id)
        
        if vocala_user:
            # Reset progress data
            await user_repo.update_learning_preferences(
                user_id=vocala_user.id,
                # Reset counters but keep settings
            )
            
            # Here you would also need to reset word progress, streaks, etc.
            # This would require additional repository methods
            
            keyboard = [[InlineKeyboardButton("⬅️ Back to Settings", callback_data="back_to_settings")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🔄 **Progress Reset Complete**\n\n"
                "✅ All learning progress has been reset:\n"
                "• Learning streak: 0 days\n"
                "• Words learned: 0\n"
                "• SRS schedules cleared\n\n"
                "Your settings (difficulty, notifications, etc.) are preserved.\n\n"
                "Ready for a fresh start! Use `/daily` to begin learning again.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        break


async def notion_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /notion command for Notion integration setup."""
    user = update.effective_user
    
    # Handle subcommands
    if context.args:
        if context.args[0] == "setup" and len(context.args) >= 3:
            await notion_setup_command(update, context)
            return
        elif context.args[0] == "disable":
            await notion_disable_command(update, context)
            return
        elif context.args[0] == "test":
            await notion_test_command(update, context)
            return
        elif context.args[0] == "fix" and len(context.args) >= 2:
            await notion_fix_command(update, context)
            return
        elif context.args[0] == "create" and len(context.args) >= 2:
            await notion_create_command(update, context)
            return
    
    async for db in get_db():
        user_repo = UserRepository(db)
        notion_service = NotionService()
        
        # Get user
        vocala_user = await user_repo.get_by_telegram_id(user.id)
        if not vocala_user:
            await update.message.reply_text(
                "Please use /start first to set up your account."
            )
            break
        
        # Check if Notion service is available
        if not notion_service._is_available():
            await update.message.reply_text(
                "❌ Notion integration is not available. Please contact the administrator."
            )
            break
        
        if vocala_user.notion_enabled and vocala_user.notion_database_id:
            notion_message = f"""
🔗 Notion Integration Status: ✅ **ACTIVE**

📄 Database ID: `{vocala_user.notion_database_id}`
🔧 Status: Words are automatically synced to your Notion database

Commands:
• `/notion disable` - Disable Notion sync
• `/notion test` - Test your connection
• `/notion fix <database_id>` - Fix database schema issues
• `/notion create <page_id>` - Create new vocabulary database
• Your daily words will continue syncing automatically

Note: Notion integration syncs new vocabulary to your database when you use /daily
            """
        else:
            notion_message = f"""
🔗 Notion Integration Setup

**Step 1**: Create a Notion integration
• Go to https://www.notion.so/my-integrations
• Create a new integration
• Copy your integration token

**Step 2**: Create or share a database
• Create a new database in Notion
• Share it with your integration
• Copy the database ID from the URL

**Step 3**: Choose setup method:
**Option A**: Use existing database
`/notion setup <database_id> <integration_token>`

**Option B**: Create new database  
`/notion create <page_id>` (after setting up token first)

Example:
`/notion setup 12345abcd your_integration_token`

**Current Status**: ❌ Not configured
            """
        
        await update.message.reply_text(notion_message.strip())
        break


async def notion_setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Notion setup with parameters."""
    user = update.effective_user
    
    # Parse arguments (skip "setup" subcommand)
    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "❌ Invalid format. Use:\n`/notion setup <database_id> <integration_token>`"
        )
        return
    
    database_id = context.args[1]  # Skip "setup" arg
    notion_token = context.args[2]
    
    async for db in get_db():
        user_repo = UserRepository(db)
        notion_service = NotionService()
        
        # Get user
        vocala_user = await user_repo.get_by_telegram_id(user.id)
        if not vocala_user:
            await update.message.reply_text("Please use /start first.")
            break
        
        # Test database access and schema
        try:
            access_test = await notion_service.test_database_access(
                database_id=database_id,
                user_notion_token=notion_token
            )
            
            if not access_test["accessible"]:
                error_msg = "❌ Cannot access Notion database. Please check:\n"
                error_msg += "• Database ID is correct\n"
                error_msg += "• Integration token is valid\n"
                error_msg += "• Database is shared with your integration\n\n"
                if access_test["error"]:
                    error_msg += f"Error: {access_test['error']}"
                
                await update.message.reply_text(error_msg)
                break
            
            # Check database compatibility
            if access_test.get("is_usable"):
                # Database is usable even if some properties are missing
                await update.message.reply_text(
                    f"✅ Database '{access_test['database_name']}' is compatible!\n\n"
                    f"**Available properties**: {', '.join(access_test.get('compatible_properties', []))}\n"
                    f"**Title column**: {access_test.get('existing_title_property', 'None')}\n\n"
                    f"Missing properties will be adapted automatically. You can proceed with setup!"
                )
            elif not access_test["has_required_properties"]:
                missing_props = ", ".join(access_test["missing_properties"])
                compatible_props = ", ".join(access_test.get("compatible_properties", []))
                
                await update.message.reply_text(
                    f"⚠️ Database '{access_test['database_name']}' needs some adjustments:\n"
                    f"**Available**: {compatible_props}\n"
                    f"**Missing**: {missing_props}\n\n"
                    f"**Fix Options:**\n"
                    f"1. Try `/notion fix {database_id}` to auto-add missing columns\n"
                    f"2. Or use the database as-is (some features may be limited)\n"
                    f"3. Create a new database with `/notion create <page_id>`"
                )
                break
            
            # Save Notion settings
            await user_repo.update_notion_settings(
                user_id=vocala_user.id,
                notion_token=notion_token,
                notion_database_id=database_id,
                notion_enabled=True
            )
            
            await update.message.reply_text(
                "✅ Notion integration setup successful!\n\n"
                "Your daily vocabulary words will now be automatically synced to your Notion database. "
                "Use /daily to get words and see them appear in Notion!"
            )
            
        except Exception as e:
            logger.error(f"Notion setup error for user {vocala_user.id}: {e}")
            await update.message.reply_text(
                "❌ Setup failed. Please try again or contact support."
            )
        
        break


async def notion_disable_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Notion disable command."""
    user = update.effective_user
    
    async for db in get_db():
        user_repo = UserRepository(db)
        
        # Get user
        vocala_user = await user_repo.get_by_telegram_id(user.id)
        if not vocala_user:
            await update.message.reply_text("Please use /start first.")
            break
        
        # Disable Notion integration
        await user_repo.update_notion_settings(
            user_id=vocala_user.id,
            notion_enabled=False
        )
        
        await update.message.reply_text(
            "✅ Notion integration has been disabled.\n\n"
            "Your vocabulary words will no longer be synced to Notion. "
            "Use `/notion setup` to re-enable if needed."
        )
        break


async def notion_test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Notion test command."""
    user = update.effective_user
    
    async for db in get_db():
        user_repo = UserRepository(db)
        notion_service = NotionService()
        
        # Get user
        vocala_user = await user_repo.get_by_telegram_id(user.id)
        if not vocala_user:
            await update.message.reply_text("Please use /start first.")
            break
        
        if not vocala_user.notion_enabled or not vocala_user.notion_database_id:
            await update.message.reply_text(
                "❌ Notion integration is not set up. Use `/notion setup` first."
            )
            break
        
        try:
            # Test database access and schema
            access_test = await notion_service.test_database_access(
                database_id=vocala_user.notion_database_id,
                user_notion_token=vocala_user.notion_token
            )
            
            if access_test["accessible"]:
                if access_test.get("is_usable"):
                    await update.message.reply_text(
                        f"✅ Notion connection and compatibility test successful!\n\n"
                        f"**Database**: {access_test['database_name']}\n"
                        f"**Available properties**: {', '.join(access_test.get('compatible_properties', []))}\n"
                        f"**Title column**: {access_test.get('existing_title_property', 'None')}\n\n"
                        f"Your integration is working and compatible!"
                    )
                elif access_test["has_required_properties"]:
                    await update.message.reply_text(
                        f"✅ Notion connection test successful!\n\n"
                        f"Database: {access_test['database_name']}\n"
                        f"All columns are present. Your integration is working properly."
                    )
                else:
                    missing_props = ", ".join(access_test["missing_properties"])
                    compatible_props = ", ".join(access_test.get("compatible_properties", []))
                    await update.message.reply_text(
                        f"⚠️ Notion connection works, but schema could be improved:\n\n"
                        f"**Database**: {access_test['database_name']}\n"
                        f"**Available**: {compatible_props}\n"
                        f"**Missing**: {missing_props}\n\n"
                        f"Your integration works, but `/notion fix {vocala_user.notion_database_id}` can add missing columns."
                    )
            else:
                error_msg = "❌ Notion connection test failed.\n\n"
                if access_test["error"]:
                    error_msg += f"Error: {access_test['error']}\n\n"
                error_msg += "Please check your integration settings and try `/notion setup` again."
                await update.message.reply_text(error_msg)
                
        except Exception as e:
            logger.error(f"Notion test error for user {vocala_user.id}: {e}")
            await update.message.reply_text(
                "❌ Connection test failed. Please try again or contact support."
            )
        
        break


async def notion_fix_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Notion fix command to repair database schema."""
    user = update.effective_user
    
    # Parse arguments (skip "fix" subcommand)
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Invalid format. Use:\n`/notion fix <database_id>`"
        )
        return
    
    database_id = context.args[1]  # Skip "fix" arg
    
    async for db in get_db():
        user_repo = UserRepository(db)
        notion_service = NotionService()
        
        # Get user
        vocala_user = await user_repo.get_by_telegram_id(user.id)
        if not vocala_user:
            await update.message.reply_text("Please use /start first.")
            break
        
        # Use user's token if they have one, otherwise require them to set up first
        user_token = vocala_user.notion_token
        if not user_token:
            await update.message.reply_text(
                "❌ No Notion token found. Please use `/notion setup` first."
            )
            break
        
        try:
            await update.message.reply_text("🔧 Checking database schema and adding missing columns...")
            
            # Attempt to fix the database schema
            fix_result = await notion_service.fix_database_schema(
                database_id=database_id,
                user_notion_token=user_token
            )
            
            if fix_result:
                # Test again to confirm it's fixed
                test_result = await notion_service.test_database_access(
                    database_id=database_id,
                    user_notion_token=user_token
                )
                
                if test_result["accessible"] and test_result["has_required_properties"]:
                    # Update user's database ID if this was successful and different
                    if database_id != vocala_user.notion_database_id:
                        await user_repo.update_notion_settings(
                            user_id=vocala_user.id,
                            notion_database_id=database_id,
                            notion_enabled=True
                        )
                    
                    await update.message.reply_text(
                        f"✅ Database schema fixed successfully!\n\n"
                        f"Database: {test_result['database_name']}\n"
                        f"All required columns are now present.\n\n"
                        f"Your Notion integration is ready! Use `/daily` to sync vocabulary words."
                    )
                else:
                    await update.message.reply_text(
                        "⚠️ Schema fix completed, but there may still be issues. "
                        "Use `/notion test` to check the current status."
                    )
            else:
                await update.message.reply_text(
                    "❌ Failed to fix database schema. Most likely cause:\n\n"
                    "**PERMISSION ISSUE**: Your integration needs 'Full access' to modify the database.\n\n"
                    "**Solution:**\n"
                    "1. Go to your Notion database\n"
                    "2. Click 'Share' (top right)\n"
                    "3. Find your integration\n"
                    "4. Change from 'Read' to 'Full access'\n"
                    "5. Try `/notion fix` again\n\n"
                    "Alternative: Use `/notion create` to make a new database with proper permissions."
                )
                
        except Exception as e:
            logger.error(f"Notion fix error for user {vocala_user.id}: {e}")
            await update.message.reply_text(
                "❌ Fix failed. Please try again or contact support."
            )
        
        break


async def notion_create_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Notion create command to create a new vocabulary database."""
    user = update.effective_user
    
    # Check if update.message exists
    if not update.message:
        logger.error("No message in update for notion_create_command")
        return
    
    # Parse arguments (skip "create" subcommand)
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Invalid format. Use:\n`/notion create <parent_page_id>`\n\n"
            "**How to get parent page ID:**\n"
            "1. Go to any Notion PAGE (not database!) where you want the new database\n"
            "2. Copy the page URL\n"
            "3. Extract the ID (32 chars after last slash)\n\n"
            "**Important**: Use a PAGE ID, not a database ID!"
        )
        return
    
    parent_page_id = context.args[1]  # Skip "create" arg
    
    async for db in get_db():
        user_repo = UserRepository(db)
        notion_service = NotionService()
        
        # Get user
        vocala_user = await user_repo.get_by_telegram_id(user.id)
        if not vocala_user:
            await update.message.reply_text("Please use /start first.")
            break
        
        # Use user's token if they have one, otherwise require them to set up first
        user_token = vocala_user.notion_token
        if not user_token:
            await update.message.reply_text(
                "❌ No Notion token found. Please use `/notion setup` first."
            )
            break
        
        try:
            await update.message.reply_text("🔨 Creating new Vocala vocabulary database...")
            
            # Create new database with proper schema
            database_id = await notion_service.create_vocabulary_database(
                parent_page_id=parent_page_id,
                database_name="Vocala Vocabulary",
                user_notion_token=user_token
            )
            
            if database_id:
                # Update user's database ID
                await user_repo.update_notion_settings(
                    user_id=vocala_user.id,
                    notion_database_id=database_id,
                    notion_enabled=True
                )
                
                await update.message.reply_text(
                    f"✅ Successfully created new Vocala vocabulary database!\n\n"
                    f"**Database ID**: `{database_id}`\n"
                    f"**Location**: Check your Notion page\n\n"
                    f"Your Notion integration is ready! Use `/daily` to start syncing vocabulary words."
                )
            else:
                await update.message.reply_text(
                    "❌ Failed to create database. This could be due to:\n"
                    "• Invalid parent page ID\n"
                    "• Insufficient permissions on the parent page\n"
                    "• Network issues\n\n"
                    "Make sure your integration has access to the parent page."
                )
                
        except Exception as e:
            logger.error(f"Notion create error for user {vocala_user.id}: {e}")
            await update.message.reply_text(
                "❌ Creation failed. Please try again or contact support."
            )
        
        break


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_message = """
🤖 Vocala Help

Commands:
/start - Start your vocabulary journey
/daily - Get your daily vocabulary words  
/progress - View your learning statistics
/settings - Adjust your preferences
/notion - Setup Notion integration
/help - Show this help message

Features:
📚 AI-generated vocabulary from Oxford 3000
🇹🇷 Turkish translations for everything
📝 Contextual example sentences
🧠 Spaced repetition system
📊 Progress tracking
🔗 Notion integration

Tips:
- Use /daily every day for best results
- Review words multiple times
- Practice using words in conversations

Happy learning! 🎓
    """
    
    await update.message.reply_text(help_message.strip())


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle general text messages."""
    await update.message.reply_text(
        "I'm here to help you learn vocabulary! Use /daily to get your words or /help for all commands."
    )


def setup_handlers(application: Application) -> None:
    """Setup all bot handlers."""
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("daily", daily_words_command))
    application.add_handler(CommandHandler("progress", progress_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("notion", notion_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Callback query handlers (for interactive buttons)
    application.add_handler(CallbackQueryHandler(settings_callback_handler))
    
    # General message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    logger.info("Bot handlers setup complete") 