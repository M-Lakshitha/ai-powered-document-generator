"""
Configuration management with environment variables
"""
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # API Keys
    GROQ_API_KEY: str
    
    # File handling
    UPLOAD_DIR: Path = Path("uploads")
    OUTPUT_DIR: Path = Path("outputs")
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: set = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.go', '.rs', '.html', '.css'}
    
    # LLM settings
    MAX_CHUNK_TOKENS: int = 6000
    MODEL_NAME: str = "llama-3.3-70b-versatile"  # ✅ FIXED: Removed "groq/" prefix
    TEMPERATURE: float = 0.1
    MAX_RETRIES: int = 3
    
    # Processing
    MAX_PARALLEL_AGENTS: int = 3
    CHUNK_BATCH_SIZE: int = 5
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# ✅ AUTO-CREATE DIRECTORIES
settings.UPLOAD_DIR.mkdir(exist_ok=True)
settings.OUTPUT_DIR.mkdir(exist_ok=True)

print(f"✓ Upload directory: {settings.UPLOAD_DIR.absolute()}")
print(f"✓ Output directory: {settings.OUTPUT_DIR.absolute()}")
print(f"✓ Using Groq model: {settings.MODEL_NAME}")  # ✅ NEW: Show which model