"""
Main FastAPI application with Telegram bot integration.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update
from telegram.ext import Application

from app.core.config import settings
from app.db.database import init_db, close_db
from app.bot.handlers import setup_handlers

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format=settings.log_format
)
logger = logging.getLogger(__name__)

# Global telegram application instance
telegram_app: Application = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting Vocala application...")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Initialize Telegram bot
    global telegram_app
    try:
        telegram_app = Application.builder().token(settings.telegram_bot_token).build()
        
        # Setup bot handlers
        setup_handlers(telegram_app)
        
        # Initialize the bot
        await telegram_app.initialize()
        await telegram_app.start()
        
        # Setup webhook or polling
        if settings.telegram_webhook_url:
            await setup_webhook(telegram_app)
            logger.info(f"Telegram webhook configured: {settings.telegram_webhook_url}")
        else:
            # Start polling in background for development
            asyncio.create_task(start_polling(telegram_app))
            logger.info("Telegram polling started")
            
        logger.info("Telegram bot initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Telegram bot: {e}")
        raise
    
    logger.info("Vocala application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Vocala application...")
    
    # Stop Telegram bot
    if telegram_app:
        try:
            await telegram_app.stop()
            await telegram_app.shutdown()
            logger.info("Telegram bot stopped")
        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}")
    
    # Close database connections
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
    
    logger.info("Vocala application shutdown complete")


async def setup_webhook(telegram_app: Application):
    """Setup Telegram webhook."""
    webhook_url = f"{settings.telegram_webhook_url}/webhook"
    await telegram_app.bot.set_webhook(
        url=webhook_url,
        secret_token=settings.telegram_webhook_secret
    )


async def start_polling(telegram_app: Application):
    """Start polling for Telegram updates."""
    try:
        await telegram_app.updater.start_polling()
        logger.info("Telegram polling started successfully")
    except Exception as e:
        logger.error(f"Error in Telegram polling: {e}")


# Create FastAPI application
app = FastAPI(
    title="Vocala",
    description="Advanced AI-powered Telegram bot for learning English vocabulary",
    version=settings.version,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Vocala - AI-powered English vocabulary learning bot",
        "version": settings.version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.version,
        "telegram_bot": "active" if telegram_app else "inactive"
    }


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Telegram webhook endpoint."""
    if not telegram_app:
        return {"error": "Telegram bot not initialized"}
    
    try:
        # Verify webhook secret if configured
        if settings.telegram_webhook_secret:
            secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if secret_token != settings.telegram_webhook_secret:
                logger.warning("Invalid webhook secret token")
                return {"error": "Invalid secret token"}
        
        # Get update data
        update_data = await request.json()
        update = Update.de_json(update_data, telegram_app.bot)
        
        # Process the update
        await telegram_app.process_update(update)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"error": "Internal server error"}


# Include API routes if you have any
# from app.api import api_router
# app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 