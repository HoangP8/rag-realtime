"""
Configuration settings for the API Gateway
"""
import os
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Medical Chatbot API"

    # CORS settings
    CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = ["*"]

    # Supabase settings
    SUPABASE_URL: str = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")

    # LiveKit settings
    LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "")
    LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "")
    LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "")

    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Deepgram settings
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")

    # Microservices URLs
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
    CONVERSATION_SERVICE_URL: str = os.getenv("CONVERSATION_SERVICE_URL", "http://localhost:8002")
    VOICE_SERVICE_URL: str = os.getenv("VOICE_SERVICE_URL", "http://localhost:8003")

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from string or list"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        """Pydantic config"""
        case_sensitive = True
        env_file = ".env.local"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

    class ConfigDict:
        # For Pydantic v2 compatibility
        env_file = [".env", ".env.local"]
        env_file_encoding = 'utf-8'
        extra = 'ignore'


settings = Settings()
