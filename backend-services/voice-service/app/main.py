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
        # Initialize RabbitMQ connection
        rabbitmq = get_rabbitmq_service()
        await rabbitmq.connect()
        logger.info("Connected to RabbitMQ")

        # Subscribe to events
        await rabbitmq.subscribe(
            queue_name="voice_events",
            routing_keys=["voice.session.*"],
            callback=handle_voice_events
        )
        logger.info("Subscribed to voice events")

    except Exception as e:
        logger.error(f"Error initializing services: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    try:
        # Close RabbitMQ connection
        rabbitmq = get_rabbitmq_service()
        await rabbitmq.close()
        logger.info("Disconnected from RabbitMQ")

        # Shutdown session manager
        session_manager = get_session_manager()
        await session_manager.shutdown()
        logger.info("Session manager shut down")

    except Exception as e:
        logger.error(f"Error cleaning up resources: {str(e)}")


async def handle_voice_events(event_data: Dict[str, Any]):
    """Handle voice events from RabbitMQ"""
    try:
        event_type = event_data.get("event_type")
        session_id = event_data.get("session_id")

        if not event_type or not session_id:
            logger.warning(f"Invalid event data: {event_data}")
            return

        logger.info(f"Received voice event: {event_type} for session {session_id}")

        # Handle different event types
        if event_type == "session_created":
            # Session already created in the service that published the event
            pass

        elif event_type == "session_deleted":
            # End session if it exists
            session_manager = get_session_manager()
            await session_manager.end_session(session_id)

        elif event_type == "session_updated":
            # Update session config
            config_data = event_data.get("config")
            if config_data:
                session_manager = get_session_manager()
                await session_manager.update_session_config(session_id, config_data)

    except Exception as e:
        logger.error(f"Error handling voice event: {str(e)}")
