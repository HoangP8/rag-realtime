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

# Add middleware to log requests and responses
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log requests and responses"""
    request_id = str(time.time())
    logger.info(f"[{request_id}] Request: {request.method} {request.url.path}")
    
    # Try to log request headers for debugging auth issues
    if request.url.path.endswith("/validate") or "/profile" in request.url.path:
        auth_header = request.headers.get("Authorization", "None")
        if auth_header:
            # Only show beginning for security
            logger.info(f"[{request_id}] Auth header present, starts with: {auth_header[:15]}...")
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(f"[{request_id}] Response: status={response.status_code}, time={process_time:.3f}s")
    return response

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
