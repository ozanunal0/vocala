# Vocala 🎯

**Advanced AI-powered Telegram bot for learning English vocabulary**

Vocala is an intelligent vocabulary learning companion that uses Large Language Models (LLMs) to dynamically generate personalized English vocabulary content with Turkish translations, example sentences, and a sophisticated Spaced Repetition System (SRS).

## ✨ Features

- **🤖 AI-Powered Content Generation**: Dynamic vocabulary generation using OpenAI GPT or Google Gemini
- **📚 Oxford 3000 Based Learning**: Vocabulary based on Oxford 3000 wordlist with difficulty levels (A1-B2)
- **🧠 Spaced Repetition System**: Intelligent review scheduling for optimal memorization
- **🇹🇷 Turkish Support**: Complete Turkish translations for English learners
- **📝 Contextual Examples**: AI-generated example sentences with translations
- **📊 Progress Tracking**: Comprehensive learning statistics and streak tracking
- **⚙️ Interactive Settings Menu**: Modern click-to-configure interface with:
  - **📅 Daily Word Count**: Choose 3, 5, 7, 10, or 15 words per day
  - **🎯 Difficulty Levels**: Visual A1-B2 selection with recommendations
  - **🔔 Smart Notifications**: One-click toggle with instant feedback
  - **⏰ Learning Reminders**: Set preferred study times (morning, noon, evening, night)
  - **🌐 Language Preferences**: Current and planned language support
  - **🔄 Progress Management**: Safe reset options with confirmation dialogs
  - **🎛️ Real-time Updates**: Settings change instantly with visual confirmation
- **🔗 Advanced Notion Integration**: Smart vocabulary database sync with:
  - **Adaptive Schema Detection**: Works with any existing Notion database
  - **Auto-Schema Repair**: Automatically adds missing columns
  - **Database Creation**: Create optimized vocabulary databases
  - **Property Type Flexibility**: Supports rich_text, select, and other types
  - **Real-time Sync**: Words automatically appear in Notion on `/daily`
  - **Interactive Management**: Full setup, test, and disable from settings menu
- **⏰ Scheduled Learning**: Daily vocabulary delivery and review reminders
- **🎯 Personalized Experience**: Adaptive difficulty and content based on user progress

## 🆕 Recent Updates

### v2.1 - Interactive Settings Revolution (Latest)
- 🎛️ **Interactive Settings Menu**: Complete overhaul from static text to dynamic interface
- 📱 **Click-to-Configure**: Instant setting changes with visual feedback and confirmation
- 🎯 **Smart Navigation**: Intuitive menu flow with back buttons and breadcrumbs  
- ⚡ **Real-time Updates**: Settings apply immediately without page reloads
- 📊 **Visual Indicators**: Color-coded difficulty levels and status displays
- 🔔 **One-Click Toggles**: Instant notification and preference switches
- ⏰ **Time Management**: Easy reminder time selection with preset options
- 🔄 **Safe Operations**: Progress reset with confirmation dialogs
- 🔗 **Integrated Notion**: Seamless Notion management from settings interface

### v2.0 - Enhanced Notion Integration
- ✅ **Adaptive Database Compatibility**: Works with any existing Notion database schema
- ✅ **Smart Schema Detection**: Automatically detects and adapts to property types
- ✅ **Auto-Schema Repair**: `/notion fix` command adds missing columns
- ✅ **Database Creation**: `/notion create` creates optimized vocabulary databases
- ✅ **Property Type Flexibility**: Supports rich_text, select, date, checkbox properties
- ✅ **Enhanced Error Handling**: Clear troubleshooting guidance and error messages
- ✅ **Real-time Sync**: Vocabulary automatically syncs to Notion on `/daily` command
- ✅ **Comprehensive Testing**: `/notion test` validates connection and compatibility

### Bot Status
- 🟢 **Core Bot**: Fully functional (vocabulary generation, SRS, progress tracking)
- 🟢 **Interactive Settings**: Complete menu system with real-time updates
- 🟢 **LLM Integration**: Working with Google Gemini and OpenAI
- 🟢 **Database**: SQLite/PostgreSQL support with migrations
- 🟢 **Notion Integration**: Advanced integration with auto-adaptation and settings UI

## 🏗️ Architecture

### Technology Stack
- **Backend**: FastAPI with async/await
- **Bot Framework**: python-telegram-bot v20.x with interactive inline keyboards
- **Database**: PostgreSQL with SQLAlchemy async
- **Cache/Broker**: Redis for Celery tasks
- **Task Queue**: Celery for background jobs
- **LLM Integration**: OpenAI GPT & Google Gemini
- **User Interface**: Modern Telegram inline keyboards with callback handlers
- **Database Migrations**: Alembic
- **Dependency Management**: Poetry
- **Containerization**: Docker & Docker Compose

### Core Components
- **LLM Service**: Central AI content generation with multi-provider support
- **Word Management**: Cache-or-generate strategy for vocabulary
- **SRS System**: Comprehensive spaced repetition implementation
- **Interactive Telegram Bot**: Modern learning interface with:
  - Click-to-configure settings menu
  - Real-time callback handling
  - Visual feedback and confirmations
  - Intuitive navigation system
- **Notion Integration**: Optional vocabulary database sync with settings UI
- **Background Tasks**: Scheduled learning and maintenance

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- OpenAI API Key or Google AI API Key

### 1. Clone the Repository
```bash
git clone git@github.com:ozanunal0/Vocala.git
cd Vocala
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 3. Install Dependencies
```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### 4. Database Setup
```bash
# Start database and Redis (using Docker)
docker-compose up -d db redis

# Run database migrations
poetry run alembic upgrade head
```

### 5. Start the Application

#### Option A: Development (Local)
```bash
# Start the main application
poetry run uvicorn app.main:app --reload

# Start Celery worker (separate terminal)
poetry run celery -A app.tasks.celery_app worker --loglevel=info

# Start Celery beat scheduler (separate terminal)  
poetry run celery -A app.tasks.celery_app beat --loglevel=info
```

#### Option B: Production (Docker)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app
```

## ⚙️ Configuration

### Required Environment Variables

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./vocala.db

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# LLM API (choose one or both)
OPENAI_API_KEY=your_openai_api_key
GOOGLE_AI_API_KEY=your_google_ai_api_key

# Security
SECRET_KEY=your_secret_key_for_jwt_tokens
```

### Optional Environment Variables

```bash
# Telegram Webhook (for production)
TELEGRAM_WEBHOOK_URL=https://yourdomain.com
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret

# Notion Integration
NOTION_API_KEY=your_notion_integration_key

# LLM Configuration
LLM_PROVIDER=openai  # openai, google, or mock
OPENAI_MODEL=gpt-3.5-turbo
GOOGLE_AI_MODEL=gemini-2.5

# Learning System
DAILY_WORD_COUNT=5
OXFORD_3000_DIFFICULTY=B1_B2

# Application
DEBUG=false
LOG_LEVEL=INFO
```

## 🤖 Bot Usage

### Basic Commands
- `/start` - Initialize your learning journey
- `/daily` - Get your daily vocabulary words (main feature)
- `/progress` - View your learning statistics
- `/settings` - **Interactive settings menu** with click-to-configure options
- `/help` - Show all available commands

### Interactive Settings Menu (`/settings`)
The settings command now opens a **modern interactive interface** with clickable buttons:

**🎛️ Main Settings Panel:**
- **📅 Daily Words**: Instantly adjust word count (3, 5, 7, 10, 15 words)
- **🎯 Difficulty Level**: Visual A1-B2 selection with color indicators
- **🔔 Notifications**: One-click ON/OFF toggle with immediate feedback
- **⏰ Learning Time**: Set reminder times (morning, noon, evening, night)
- **🌐 Language**: Current and upcoming language support info
- **🔗 Notion Integration**: Complete management interface
- **🔄 Reset Progress**: Safe reset with confirmation dialog

**💡 Key Benefits:**
- ⚡ **Instant Updates**: No need to remember command syntax
- 🎯 **Visual Guidance**: Clear recommendations for each setting
- 🔙 **Smart Navigation**: Easy back buttons and menu flow
- ✅ **Confirmation**: Visual feedback for every change

### Notion Integration Commands
- `/notion` - Show Notion integration status and setup guide
- `/notion setup <database_id> <token>` - Connect existing Notion database
- `/notion test` - Test your Notion connection and compatibility
- `/notion fix <database_id>` - Auto-fix database schema issues
- `/notion create <page_id>` - Create new vocabulary database in Notion
- `/notion disable` - Disable Notion synchronization

*Note: Notion management is also available through the interactive settings menu!*

### Learning Flow
1. **Start**: Use `/start` to create your account
2. **Configure**: Use `/settings` to personalize your experience with the interactive menu
3. **Daily Learning**: Use `/daily` to receive AI-generated vocabulary
4. **Notion Sync**: Words automatically sync to your Notion database (if configured)
5. **Review**: Words are scheduled for review using SRS algorithm
6. **Progress**: Track your streak and mastered words with `/progress`

### Notion Integration Setup
1. **Create Integration**: Go to https://www.notion.so/my-integrations
2. **Get Token**: Copy your integration token
3. **Setup Options**:
   - **Existing Database**: `/notion setup <database_id> <token>`
   - **New Database**: `/notion create <page_id>` (after setup)
4. **Auto-sync**: Daily words automatically appear in your Notion database!

### Example Workflows

**Interactive Settings Menu Visual:**
```
⚙️ Interactive Settings Menu

👤 User: John Doe
📊 Progress: 45 words learned, 7 day streak

📋 Current Settings:
• Daily word count: 5 words
• Difficulty level: B1
• Notifications: Enabled
• Preferred time: 18:00
• Notion sync: Active

┌─────────────────────────────────────┐
│ [📅 Daily Words: 5] [🎯 Level: B1]  │
│ [🔔 Notifications: ON] [🌐 Turkish] │
│ [🔗 Notion Integration] [⏰ 18:00]  │
│ [🔄 Reset Progress] [✅ Close Menu] │
└─────────────────────────────────────┘

User: [Clicks "📅 Daily Words: 5"]  
Bot: 📅 Daily Word Count
     Choose your preferred daily word count:
     
     ┌─────────────────────────────────┐
     │ [3 words] [5 words] [7 words]   │
     │     [10 words] [15 words]       │
     │     [⬅️ Back to Settings]       │
     └─────────────────────────────────┘

User: [Clicks "10 words"]
Bot: ✅ Daily Word Count Updated
     You will now receive 10 words per day.
     
     [⬅️ Back to Settings]
```

**Traditional Notion Setup:**
```
User: /notion setup abc123def456 secret_xyz123
Bot: ⚠️ Database 'My Vocab' needs some adjustments:
     Available: Name (title), Translation (rich_text)
     Missing: Part of Speech, Definition, Level, Examples
     
     Fix Options:
     1. Try /notion fix abc123def456 to auto-add missing columns

User: /notion fix abc123def456  
Bot: ✅ Database schema fixed successfully!
     All required columns are now present.

User: /daily
Bot: 📚 Your Daily Vocabulary (10 words)
     [Words appear in Telegram AND automatically sync to Notion database]
```

**Settings Menu Notion Management:**
```
User: /settings → [Clicks "🔗 Notion Integration"]
Bot: 🔗 Notion Integration
     Status: 🟢 Connected
     [Shows: Setup Guide, Test Connection, Disable options]

User: [Clicks "🔧 Test Connection"]
Bot: ✅ Notion Test Successful
     Database: My Vocabulary Database
     Status: Fully compatible
```

## 🛠️ Development

### Project Structure
```
vocala/
├── app/
│   ├── core/           # Configuration and settings
│   ├── db/             # Database models and repositories
│   ├── llm_interface/  # LLM service integration
│   ├── services/       # Business logic services
│   ├── bot/            # Telegram bot handlers
│   ├── tasks/          # Celery background tasks
│   └── main.py         # FastAPI application
├── alembic/            # Database migrations
├── tests/              # Test suite
├── docker-compose.yml  # Docker services
├── Dockerfile          # Application container
└── pyproject.toml      # Dependencies and configuration
```

### Key Services
- **LLMService**: Generates vocabulary using AI with caching
- **WordManagementService**: Primary LLM consumer, handles cache/generation
- **SRSService**: Manages spaced repetition and learning progress
- **UserService**: User management and preferences
- **Interactive Bot Handlers**: Modern Telegram interface with:
  - Dynamic inline keyboard generation
  - Real-time callback query routing
  - Visual setting confirmations and navigation
  - Context-aware menu state management
  - Safe setting updates with validation
- **NotionService**: Advanced Notion database integration with:
  - Adaptive schema detection and compatibility checking
  - Automatic database creation with proper vocabulary schema
  - Schema repair for existing databases
  - Smart property type handling (rich_text, select, etc.)
  - Real-time vocabulary synchronization
  - Interactive settings menu integration

### Running Tests
```bash
# Install test dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html
```

### Code Quality
```bash
# Format code
poetry run black app/
poetry run isort app/

# Lint code  
poetry run ruff check app/

# Type checking
poetry run mypy app/
```

## 📊 Database Schema

### Core Models
- **User**: Telegram users with learning preferences and progress
- **Word**: LLM-generated vocabulary cache with metadata
- **Example**: AI-generated example sentences for words
- **UserWordProgress**: SRS tracking with detailed learning metrics

### Key Features
- **LLM Caching**: Efficient caching of AI-generated content
- **SRS Implementation**: Sophisticated spaced repetition algorithm
- **Progress Tracking**: Detailed learning analytics
- **Multi-provider LLM**: Support for multiple AI providers

## 🔧 Advanced Configuration

### LLM Provider Setup

#### OpenAI
```bash
OPENAI_API_KEY=sk-your-openai-key
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-3.5-turbo  # or gpt-4
```

#### Google Gemini
```bash
GOOGLE_AI_API_KEY=your-google-ai-key
LLM_PROVIDER=google
GOOGLE_AI_MODEL=gemini-pro
```

### Notion Integration

#### Environment Setup
```bash
# Required for Notion integration
NOTION_API_KEY=your_notion_integration_token
ENABLE_NOTION=true
```

#### User Setup Methods

**Method 1: Use Existing Database**
```
/notion setup <database_id> <user_token>
```
- Works with any Notion database
- Automatically adapts to existing schema
- Adds missing columns if permissions allow

**Method 2: Create New Database**
```
/notion create <page_id>
```
- Creates optimized vocabulary database
- Perfect schema from the start
- No compatibility issues

#### Required Database Properties
The bot automatically handles these properties:
- **Title Property** (any name) - For English words
- **Turkish Translation** (Text/Rich Text) - Turkish meanings
- **Part of Speech** (Text/Select) - Word types
- **Definition** (Text/Rich Text) - English definitions
- **Level** (Text/Select) - Difficulty levels (A1, A2, B1, B2)
- **Examples** (Text/Rich Text) - Example sentences

Optional properties:
- **Date Added** (Date) - When word was added
- **Mastered** (Checkbox) - Learning progress

#### Troubleshooting

**Schema Issues**
- Use `/notion test` to check compatibility
- Use `/notion fix <database_id>` to add missing columns
- Ensure integration has "Full access" permissions

**Permission Errors**
- Database must be shared with your integration
- Integration needs "Full access" (not just "Read")
- For existing databases: Share → Update permissions

**Property Type Mismatches**
- Bot automatically adapts to existing property types
- Rich text and select properties are both supported
- Missing properties are gracefully handled

### Production Deployment
- Use webhook instead of polling for Telegram
- Set up proper logging and monitoring
- Configure Redis persistence
- Use environment-specific settings
- Set up SSL/TLS for webhooks

## 📈 Monitoring

### Health Checks
- `GET /health` - Application health status
- `GET /` - Basic application info

### Logs
- Application logs via Python logging
- Celery task logs
- Database query logs (if enabled)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support, please:
1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information

## 🚀 Roadmap

- [x] **Interactive Settings Menu** ✅ *Completed in v2.1*
- [ ] Interactive quizzes and games
- [ ] Voice pronunciation features  
- [ ] Mobile app companion
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Integration with more learning platforms
- [ ] Custom time input via text message
- [ ] Vocabulary review system with interactive cards
- [ ] Learning streak rewards and achievements

---

## 📱 **What's New in v2.1?**

The **Interactive Settings Revolution** transforms how users configure Vocala:

**Before:** Static text requiring command memorization  
**After:** Modern click-to-configure interface with instant feedback

**🚀 Key Improvements:**
- ⚡ **Zero Command Learning**: Click buttons instead of typing commands
- 🎯 **Visual Guidance**: Color-coded levels and clear recommendations  
- 📱 **Mobile-Friendly**: Intuitive interface works perfectly on phones
- ✅ **Instant Feedback**: See changes applied immediately with confirmations
- 🔙 **Smart Navigation**: Easy back buttons and logical menu flow

**🎛️ Try the New Interface:**
```bash
# Start the bot and try the interactive settings
/settings
```

The interface automatically adapts to your current configuration and provides contextual help for every option!

---

**Happy Learning! 📚✨** 