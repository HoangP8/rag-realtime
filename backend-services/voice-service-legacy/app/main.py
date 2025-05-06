"""
Voice Service for Medical Chatbot
Main FastAPI application entry point
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Dict, Any

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.config import settings
from app.dependencies import get_rabbitmq_service, get_session_manager
from app.messaging.rabbitmq import RabbitMQService
from app.realtime.session_manager import SessionManager

app = FastAPI(
    title="Medical Chatbot Voice Service",
    description="Voice processing service for Medical Chatbot",
    version="0.1.0",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(router)

# Set up logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to console
        RotatingFileHandler(
            os.path.join(log_dir, "voice-service.log"),
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
    ]
)

# Get logger for this module
logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"message": "Medical Chatbot Voice Service is running"}


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Initialize RabbitMQ connection but don't subscribe to events
        # This is just for future integration - not used in current phase
        try:
            rabbitmq = get_rabbitmq_service()
            # Attempt to connect but don't fail the app if RabbitMQ is not available
            await rabbitmq.connect()
            logger.info("Connected to RabbitMQ (for future integration)")
        except Exception as e:
            # Just log the error but don't let it affect the app
            logger.warning(f"RabbitMQ connection failed, but app will continue: {str(e)}")

        # Note: Event subscription is disabled for current phase
        # Will be implemented in next phase
        # await rabbitmq.subscribe(
        #     queue_name="voice_events",
        #     routing_keys=["voice.session.*"],
        #     callback=handle_voice_events
        # )

    except Exception as e:
        logger.error(f"Error initializing services: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    try:
        # Close RabbitMQ connection if it was established
        try:
            rabbitmq = get_rabbitmq_service()
            await rabbitmq.close()
            logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            logger.warning(f"Error closing RabbitMQ connection, but shutdown will continue: {str(e)}")

        # Shutdown session manager
        session_manager = get_session_manager()
        await session_manager.shutdown()
        logger.info("Session manager shut down")

    except Exception as e:
        logger.error(f"Error cleaning up resources: {str(e)}")


async def handle_voice_events(event_data: Dict[str, Any]):
    """
    Handle voice events from RabbitMQ

    Note: This function is currently a placeholder for future implementation.
    In the current phase, RabbitMQ integration is defined but not actively used.
    The actual event handling will be implemented in the next phase.
    """
    # This is a placeholder for future implementation
    # The function is defined but not currently used

    # Future implementation will handle:
    # - session_created: Notification that a session was created elsewhere
    # - session_deleted: Request to end a session
    # - session_updated: Request to update session configuration

    logger.debug(f"RabbitMQ event handler called (inactive in current phase): {event_data}")
    pass
