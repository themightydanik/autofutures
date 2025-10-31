# backend/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

# ==================== ENUMS ====================

class TradeType(str, Enum):
    MARGIN = "margin"
    ARBITRAGE = "arbitrage"

class StrategyType(str, Enum):
    # Margin strategies
    BREAKOUT = "breakout"
    RETEST = "retest"
    TREND = "trend"
    # Arbitrage strategies
    INTER_EXCHANGE = "inter-exchange"
    TRIANGULAR = "triangular"
    INTRA_EXCHANGE = "intra-exchange"

class TradeSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"

class TradeStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PENDING = "pending"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"

# ==================== AUTH MODELS ====================

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    token: str
    user_id: str
    expires_at: datetime

# ==================== USER MODELS ====================

class ExchangeAPI(BaseModel):
    exchange_id: str
    api_key: str
    secret_key: str
    passphrase: Optional[str] = None

class UserSettings(BaseModel):
    trade_type: TradeType
    strategy: StrategyType
    exchanges: List[str]
    api_keys: Dict[str, Dict[str, str]]
    telegram_notifications: Optional[bool] = False
    telegram_chat_id: Optional[str] = None

# ==================== TRADING MODELS ====================

class TradeParams(BaseModel):
    coin: str = "BTC"
    side: TradeSide = TradeSide.LONG
    order_size: float = Field(100.0, gt=0)
    stop_loss: float = Field(2.0, ge=0, le=100)
    take_profit: float = Field(5.0, ge=0, le=100)
    frequency: str = "medium"  # low, medium, high
    max_trades: Optional[int] = Field(10, ge=1, le=100)
    min_profit_threshold: Optional[float] = Field(0.1, ge=0)  # Минимальный профит для арбитража

class TradeOrder(BaseModel):
    order_id: str
    user_id: str
    exchange: str
    symbol: str
    side: TradeSide
    order_type: OrderType
    price: float
    amount: float
    filled_amount: float = 0.0
    status: TradeStatus
    created_at: datetime
    updated_at: datetime

class ActiveTrade(BaseModel):
    id: str
    user_id: str
    coin: str
    trade_type: str
    entry_price: float
    current_price: float
    amount: float
    pnl: float
    pnl_percent: float
    status: TradeStatus
    exchanges: List[str]
    opened_at: datetime
    updated_at: datetime

class CompletedTrade(BaseModel):
    id: str
    user_id: str
    coin: str
    trade_type: str
    entry_price: float
    exit_price: float
    amount: float
    pnl: float
    pnl_percent: float
    opened_at: datetime
    closed_at: datetime
    exchanges: List[str]

# ==================== BOT LOG MODELS ====================

class LogType(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    SEARCH = "search"
    BUY = "buy"
    SELL = "sell"
    TRANSFER = "transfer"
    PROFIT = "profit"

class BotLog(BaseModel):
    id: str
    user_id: str
    timestamp: datetime
    log_type: LogType
    message: str
    details: Optional[Dict] = None

# ==================== BALANCE MODELS ====================

class Balance(BaseModel):
    exchange: str
    currency: str = "USDT"
    free: float
    locked: float
    total: float
    updated_at: datetime

class TotalBalance(BaseModel):
    total_usdt: float
    balances: List[Balance]
    updated_at: datetime

# ==================== MARKET DATA MODELS ====================

class PriceData(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class CoinInfo(BaseModel):
    symbol: str
    name: str
    current_price: float
    price_change_24h: float
    volume_24h: float
    market_cap: Optional[float] = None

class ArbitrageOpportunity(BaseModel):
    coin: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    spread_percent: float
    estimated_profit: float
    timestamp: datetime

# ==================== ANALYTICS MODELS ====================

class PnLData(BaseModel):
    timestamp: datetime
    pnl: float
    pnl_percent: float
    cumulative_pnl: float

class TradingStatistics(BaseModel):
    user_id: str
    total_trades: int
    successful_trades: int
    failed_trades: int
    win_rate: float
    total_pnl: float
    total_pnl_percent: float
    best_trade: float
    worst_trade: float
    average_trade_duration: float  # в минутах
    trades_today: int
    pnl_today: float
    period_start: datetime
    period_end: datetime

# ==================== WEBSOCKET MODELS ====================

class WebSocketMessage(BaseModel):
    type: str  # update, log, trade, balance, etc.
    data: Dict
    timestamp: datetime = Field(default_factory=datetime.now)

class LiveUpdate(BaseModel):
    pnl: float
    pnl_percent: float
    active_trades: List[ActiveTrade]
    latest_logs: List[BotLog]
    balances: List[Balance]
    timestamp: datetime = Field(default_factory=datetime.now)

# ==================== STRATEGY CONFIG ====================

class StrategyConfig(BaseModel):
    strategy_type: StrategyType
    parameters: Dict  # Специфичные параметры для каждой стратегии
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy_type": "inter-exchange",
                "parameters": {
                    "min_spread": 0.5,
                    "max_slippage": 0.2,
                    "transfer_time_estimate": 300
                }
            }
        }

# ==================== NOTIFICATION MODELS ====================

class Notification(BaseModel):
    user_id: str
    title: str
    message: str
    notification_type: str  # info, success, warning, error
    read: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

class TelegramNotification(BaseModel):
    chat_id: str
    message: str
    parse_mode: str = "HTML"
