from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Azure Storage settings
    azure_storage_connection_string: Optional[str] = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    azure_storage_container_name: str = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "documents")
    azure_storage_account_name: Optional[str] = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    azure_storage_account_key: Optional[str] = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    
    # Application settings
    app_name: str = "RAG Document Upload Service"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()