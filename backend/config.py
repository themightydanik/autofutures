# backend/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Приложение
    APP_NAME: str = "AutoFutures API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Сервер
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Безопасность
    SECRET_KEY: str = "your-secret-key-change-in-production-!!!IMPORTANT!!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 часа
    
    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173", "*"]
    
    # База данных (MySQL)
    DATABASE_URL: Optional[str] = None
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "autofutures"
    
    # Redis
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Биржи - Rate Limits
    BINANCE_RATE_LIMIT: int = 1200  # requests per minute
    GATEIO_RATE_LIMIT: int = 900
    BYBIT_RATE_LIMIT: int = 120
    
    # Торговля
    MIN_ORDER_SIZE_USDT: float = 10.0
    MAX_ORDER_SIZE_USDT: float = 10000.0
    DEFAULT_SLIPPAGE: float = 0.1  # 0.1%
    
    # Telegram Bot (опционально)
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_ENABLED: bool = False
    
    # Логирование
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/autofutures.log"
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MESSAGE_QUEUE_SIZE: int = 100
    
    # Стратегии
    ARBITRAGE_MIN_SPREAD: float = 0.3  # минимальный спред для арбитража (%)
    ARBITRAGE_MAX_SLIPPAGE: float = 0.2  # максимальный slippage
    TRANSFER_FEE_ESTIMATE: float = 0.1  # оценка комиссии за перевод (%)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Создаём глобальный экземпляр настроек
settings = Settings()

# Поддерживаемые биржи
SUPPORTED_EXCHANGES = {
    'binance': {
        'name': 'Binance',
        'fees': {
            'maker': 0.1,  # 0.1%
            'taker': 0.1
        },
        'withdrawal_fees': {
            'BTC': 0.0005,
            'ETH': 0.005,
            'USDT': 1.0
        }
    },
    'gateio': {
        'name': 'Gate.io',
        'fees': {
            'maker': 0.2,
            'taker': 0.2
        },
        'withdrawal_fees': {
            'BTC': 0.001,
            'ETH': 0.01,
            'USDT': 2.0
        }
    },
    'bybit': {
        'name': 'Bybit',
        'fees': {
            'maker': 0.1,
            'taker': 0.1
        },
        'withdrawal_fees': {
            'BTC': 0.0005,
            'ETH': 0.005,
            'USDT': 1.0
        }
    }
}

# Торговые пары
TRADING_PAIRS = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT',
    'XRP/USDT', 'ADA/USDT', 'DOGE/USDT', 'MATIC/USDT',
    'DOT/USDT', 'AVAX/USDT', 'LINK/USDT', 'UNI/USDT'
]

# Интервалы для графиков
CHART_INTERVALS = {
    '1m': 60,
    '5m': 300,
    '15m': 900,
    '1h': 3600,
    '4h': 14400,
    '1d': 86400
}
