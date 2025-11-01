# backend/config.py
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # App
    APP_NAME: str = "AutoFutures API"
    VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "CHANGE-THIS-SECRET-KEY-IN-PRODUCTION-!!!IMPORTANT!!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8082", "*"]
    
    # Database (MySQL)
    DATABASE_URL: Optional[str] = None
    DB_HOST: str = "mysql"
    DB_PORT: int = 3306
    DB_USER: str = "autofutures"
    DB_PASSWORD: str = "autofutures123"
    DB_NAME: str = "autofutures"
    
    # Redis
    REDIS_URL: Optional[str] = "redis://redis:6379"
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # Trading
    MIN_ORDER_SIZE_USDT: float = 10.0
    MAX_ORDER_SIZE_USDT: float = 10000.0
    DEFAULT_SLIPPAGE: float = 0.1
    ARBITRAGE_MIN_SPREAD: float = 0.3
    
    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_ENABLED: bool = False
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/autofutures.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Supported exchanges
SUPPORTED_EXCHANGES = {
    'binance': {
        'name': 'Binance',
        'fees': {'maker': 0.1, 'taker': 0.1}
    },
    'gateio': {
        'name': 'Gate.io',
        'fees': {'maker': 0.2, 'taker': 0.2}
    },
    'bybit': {
        'name': 'Bybit',
        'fees': {'maker': 0.1, 'taker': 0.1}
    }
}
