# backend/database/models.py
from sqlalchemy import Column, String, Boolean, Float, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable для OAuth users
    google_id = Column(String(100), unique=True, nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    exchanges = relationship("ExchangeConnection", back_populates="user", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    trade_type = Column(String(20), nullable=True)  # margin, arbitrage
    strategy = Column(String(50), nullable=True)
    telegram_notifications = Column(Boolean, default=False)
    telegram_chat_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="settings")

class ExchangeConnection(Base):
    __tablename__ = "exchange_connections"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exchange_id = Column(String(20), nullable=False)  # binance, gateio, bybit
    api_key_encrypted = Column(Text, nullable=False)
    secret_key_encrypted = Column(Text, nullable=False)
    passphrase_encrypted = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="exchanges")

class TradeStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TradeSide(enum.Enum):
    BUY = "buy"
    SELL = "sell"
    LONG = "long"
    SHORT = "short"

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    trade_type = Column(String(20), nullable=False)  # arbitrage, margin, spot
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(SQLEnum(TradeSide), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    amount = Column(Float, nullable=False)
    filled_amount = Column(Float, default=0.0)
    pnl = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)
    fees = Column(Float, default=0.0)
    status = Column(SQLEnum(TradeStatus), default=TradeStatus.PENDING, index=True)
    exchanges = Column(JSON, nullable=True)  # List of exchanges for arbitrage
    strategy = Column(String(50), nullable=True)
    opened_at = Column(DateTime, default=datetime.utcnow, index=True)
    closed_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="trades")

class BotLog(Base):
    __tablename__ = "bot_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    trade_id = Column(String(36), ForeignKey("trades.id", ondelete="SET NULL"), nullable=True)
    log_type = Column(String(20), nullable=False, index=True)  # info, success, error, etc
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="sessions")

class Balance(Base):
    __tablename__ = "balances"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exchange_id = Column(String(20), nullable=False, index=True)
    currency = Column(String(10), nullable=False)
    free_balance = Column(Float, default=0.0)
    locked_balance = Column(Float, default=0.0)
    total_balance = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
