"""
Authentication Service for Medical Chatbot
Main FastAPI application entry point
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

from app.router import router
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Medical Chatbot Auth Service",
    description="Authentication service for Medical Chatbot",
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

# Include router with prefix
app.include_router(router, prefix="/api/v1/auth")

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"message": "Medical Chatbot Auth Service is running"}
