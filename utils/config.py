import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging configuration
def setup_logging():
    """Configure logging for the application"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Set specific loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)

# API Configuration
class Config:
    """Application configuration"""
    
    # API Keys
    XAI_API_KEY = os.getenv("XAI_API_KEY")
    X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
    
    # API Settings
    API_TITLE = "X-Consensus Builder API"
    API_DESCRIPTION = "API for analyzing X/Twitter debates to find common ground"
    API_VERSION = "1.0.0"
    
    # CORS Settings
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "https://*.vercel.app",
        "https://x-consensus-builder.vercel.app"
    ]
    
    # Rate Limiting
    MAX_TWEETS_PER_THREAD = 100
    REQUEST_TIMEOUT = 30.0
    MIN_REQUEST_INTERVAL = 1.0  # Minimum seconds between API requests
    RATE_LIMIT_RETRY_ATTEMPTS = 3
    RATE_LIMIT_BASE_DELAY = 1.0  # Base delay for exponential backoff
    
    # Development
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present"""
        required_vars = ["XAI_API_KEY", "X_BEARER_TOKEN"]
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True