"""
Configuration settings for the Conversation Service
"""
import os
from typing import List, Union

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    PROJECT_NAME: str = "Medical Chatbot Conversation Service"

    # CORS settings
    CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = ["*"]

    # Supabase settings
    SUPABASE_URL: str = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")

    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

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
