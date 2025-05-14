"""
Conversation Service for Medical Chatbot
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router import router
from app.config import settings

app = FastAPI(
    title="Medical Chatbot Conversation Service",
    description="Conversation management service for Medical Chatbot",
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
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"message": "Medical Chatbot Conversation Service is running"}
