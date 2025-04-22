"""
LLM Service for Medical Chatbot
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.config import settings

app = FastAPI(
    title="Medical Chatbot LLM Service",
    description="LLM integration service for Medical Chatbot",
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

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"message": "Medical Chatbot LLM Service is running"}
