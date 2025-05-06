"""
Configuration settings for the Voice Service
"""
import os
from typing import List, Union

from dotenv import load_dotenv
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()
load_dotenv(".env.local")

class Settings(BaseSettings):
    """Application settings"""
    PROJECT_NAME: str = "Medical Chatbot Voice Service"
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8003
    
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
    
    # Voice settings defaults
    DEFAULT_VOICE_ID: str = "alloy"
    DEFAULT_TEMPERATURE: float = 0.8
    DEFAULT_MAX_OUTPUT_TOKENS: int = 2048
    
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

# Create settings instance
settings = Settings()
