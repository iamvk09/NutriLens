"""
NutriLens Configuration Module
Centralizes typed settings and environment variables across backend and services.
"""

import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation and environment loading."""

    # Environment & Logging
    ENVIRONMENT: str = Field(default="development", description="Runtime environment (development, staging, production)")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Server Details
    HOST: str = Field(default="0.0.0.0", description="Backend host")
    PORT: int = Field(default=8000, description="Backend port")
    BACKEND_API_URL: str = Field(default="http://localhost:8000/api/v1", description="Public backend API URL")

    # Frontend Details
    FRONTEND_PORT: int = Field(default=8501, description="Frontend port")
    FRONTEND_APP_URL: str = Field(default="http://localhost:8501", description="Frontend application URL")

    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:8501", "http://127.0.0.1:8501", "http://localhost:3000"],
        description="Allowed CORS origins"
    )

    # Supabase Credentials
    SUPABASE_URL: Optional[str] = Field(default=None, description="Supabase project URL")
    SUPABASE_KEY: Optional[str] = Field(default=None, description="Supabase anon key")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(default=None, description="Supabase service role key (optional)")
    SUPABASE_JWT_SECRET: Optional[str] = Field(default=None, description="Supabase JWT secret for offline token verification")

    # External APIs
    USDA_API_KEY: Optional[str] = Field(default=None, description="USDA FoodData Central API key")
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash", description="Gemini model identifier for OCR and recipe generation")

    # ML Model Configuration
    MODEL_PATH: str = Field(default="./models/food_model.onnx", description="Path to ONNX model file")
    CLASS_NAMES_PATH: str = Field(default="./models/class_names.json", description="Path to class names JSON")
    MODEL_DOWNLOAD_URL: Optional[str] = Field(default=None, description="Remote URL to fetch model binary if missing")
    MODEL_EXPECTED_SHA256: Optional[str] = Field(
        default="aa6157a28f37bd797fa6e9b09e24bdd1243aa93f9fcbbc0ea3d198c0f9e6f7cd",
        description="Expected SHA256 checksum for model binary validation"
    )
    MODEL_EXPECTED_SIZE_BYTES: Optional[int] = Field(
        default=14571154,
        description="Expected model binary size in bytes"
    )

    # Request & Upload Limits
    MAX_IMAGE_SIZE_BYTES: int = Field(default=10 * 1024 * 1024, description="Max upload size (10 MB)")
    HTTP_TIMEOUT_SECONDS: float = Field(default=10.0, description="HTTP client timeout in seconds")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return []
            return [i.strip() for i in v.split(",") if i.strip()]
        return v


# Singleton settings instance
settings = Settings()
