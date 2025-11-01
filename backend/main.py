# backend/main.py (REAL VERSION)
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict
import asyncio
import json
from datetime import datetime
import uvicorn
import logging
from sqlalchemy.orm import Session

# Imports
from database.database import get_db, init_db, check_db_connection
from database.models import User, UserSettings, ExchangeConnection
from services.auth_service import AuthService
from services.oauth_service import OAuthService
from services.exchange_service import ExchangeService
from services.trade_engine import TradeEngine
from utils.encryption import encryption_service
from config import settings

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AutoFutures API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Services
exchange_service = ExchangeService()
trade_engine = TradeEngine(exchange_service)

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except:
                pass

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Pydantic models
class UserRegister(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class GoogleAuthRequest(BaseModel):
    token: str

class UserSettingsUpdate(BaseModel):
    trade_type: Optional[str] = None
    strategy: Optional[str] = None
    exchanges: Optional[List[str]] = None

class ExchangeConnect(BaseModel):
    exchange_id: str
    api_key: str
    secret_key: str
    passphrase: Optional[str] = None

class TradeParamsUpdate(BaseModel):
    coin: str = "BTC"
    side: str = "LONG"
    order_size: float = 100.0
    stop_loss: float = 2.0
    take_profit: float = 5.0
    frequency: str = "medium"

# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    try:
        auth_service = AuthService(db)
        user_id = await auth_service.verify_token(credentials.credentials)
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# ==================== STARTUP ====================

@app.on_event("startup")
async def startup_event():
    logger.info("Starting AutoFutures API...")
    if not check_db_connection():
        logger.error("Database connection failed!")
    else:
        logger.info("Database connected successfully")
        init_db()

# ==================== AUTH ENDPOINTS ====================

@app.post("/api/auth/register")
async def register(user: UserRegister, db: Session = Depends(get_db)):
    """Register new user"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.register_user(user.username, user.password, user.email)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.login_user(user.username, user.password)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/api/auth/google")
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Google OAuth login"""
    try:
        oauth_service = OAuthService()
        user_info = await oauth_service.verify_google_token(request.token)
        
        auth_service = AuthService(db)
        result = await auth_service.google_login(
            user_info['google_id'],
            user_info['email'],
            user_info['name']
        )
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/api/auth/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Logout user"""
    try:
        auth_service = AuthService(db)
        await auth_service.logout_user(credentials.credentials)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== USER ENDPOINTS ====================

@app.get("/api/user/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get user profile"""
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at.isoformat()
    }

@app.get("/api/user/settings")
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user settings"""
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        return {}
    
    exchanges = db.query(ExchangeConnection).filter(
        ExchangeConnection.user_id == current_user.id,
        ExchangeConnection.is_active == True
    ).all()
    
    return {
        "trade_type": settings.trade_type,
        "strategy": settings.strategy,
        "exchanges": [ex.exchange_id for ex in exchanges]
    }

@app.post("/api/user/settings")
async def save_settings(
    settings_data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save user settings"""
    try:
        settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
        if not settings:
            settings = UserSettings(user_id=current_user.id)
            db.add(settings)
        
        if settings_data.trade_type:
            settings.trade_type = settings_data.trade_type
        if settings_data.strategy:
            settings.strategy = settings_data.strategy
        
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# ==================== EXCHANGE ENDPOINTS ====================

@app.post("/api/exchanges/connect")
async def connect_exchange(
    request: ExchangeConnect,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Connect exchange via API keys"""
    try:
        # Encrypt API keys
        encrypted_api_key = encryption_service.encrypt(request.api_key)
        encrypted_secret = encryption_service.encrypt(request.secret_key)
        encrypted_passphrase = encryption_service.encrypt(request.passphrase) if request.passphrase else None
        
        # Save to database
        existing = db.query(ExchangeConnection).filter(
            ExchangeConnection.user_id == current_user.id,
            ExchangeConnection.exchange_id == request.exchange_id
        ).first()
        
        if existing:
            existing.api_key_encrypted = encrypted_api_key
            existing.secret_key_encrypted = encrypted_secret
            existing.passphrase_encrypted = encrypted_passphrase
            existing.is_active = True
        else:
            connection = ExchangeConnection(
                user_id=current_user.id,
                exchange_id=request.exchange_id,
                api_key_encrypted=encrypted_api_key,
                secret_key_encrypted=encrypted_secret,
                passphrase_encrypted=encrypted_passphrase,
                is_active=True
            )
            db.add(connection)
        
        db.commit()
        
        # Test connection
        decrypted_api = encryption_service.decrypt(encrypted_api_key)
        decrypted_secret = encryption_service.decrypt(encrypted_secret)
        
        await exchange_service.connect_exchange(
            current_user.id,
            request.exchange_id,
            decrypted_api,
            decrypted_secret
        )
        
        return {"success": True, "message": f"Connected to {request.exchange_id}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/exchanges/balances")
async def get_balances(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get balances from all connected exchanges"""
    try:
        # Get user's exchanges
        exchanges = db.query(ExchangeConnection).filter(
            ExchangeConnection.user_id == current_user.id,
            ExchangeConnection.is_active == True
        ).all()
        
        balances = {}
        for ex in exchanges:
            try:
                # Decrypt keys
                api_key = encryption_service.decrypt(ex.api_key_encrypted)
                secret_key = encryption_service.decrypt(ex.secret_key_encrypted)
                
                # Connect if not connected
                if current_user.id not in exchange_service.exchanges or \
                   ex.exchange_id not in exchange_service.exchanges.get(current_user.id, {}):
                    await exchange_service.connect_exchange(
                        current_user.id, ex.exchange_id, api_key, secret_key
                    )
                
                # Get balance
                balance = await exchange_service.get_balance(current_user.id, ex.exchange_id)
                balances[ex.exchange_id] = balance['total']
            except Exception as e:
                logger.error(f"Error getting balance from {ex.exchange_id}: {str(e)}")
                balances[ex.exchange_id] = 0
        
        return balances
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/exchanges/available-coins")
async def get_available_coins(
    exchange_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get available trading pairs for exchange"""
    try:
        coins = await exchange_service.get_available_pairs(current_user.id, exchange_id)
        return {"coins": coins}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== TRADING ENDPOINTS ====================

@app.post("/api/trade/start")
async def start_trading(
    params: TradeParamsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start trading bot"""
    try:
        settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
        await trade_engine.start_trading(current_user.id, settings.__dict__, params.dict())
        
        await manager.send_personal_message({
            "type": "trade_status",
            "status": "started",
            "message": "🚀 Бот запущен!"
        }, current_user.id)
        
        return {"success": True, "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/trade/stop")
async def stop_trading(current_user: User = Depends(get_current_user)):
    """Stop trading bot"""
    try:
        await trade_engine.stop_trading(current_user.id)
        
        await manager.send_personal_message({
            "type": "trade_status",
            "status": "stopped"
        }, current_user.id)
        
        return {"success": True, "status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/trade/status")
async def get_trade_status(current_user: User = Depends(get_current_user)):
    """Get trading status"""
    status = await trade_engine.get_status(current_user.id)
    return status

@app.get("/api/trade/active")
async def get_active_trades(current_user: User = Depends(get_current_user)):
    """Get active trades"""
    trades = await trade_engine.get_active_trades(current_user.id)
    return trades

@app.get("/api/trade/history")
async def get_trade_history(
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get trade history"""
    history = await trade_engine.get_trade_history(current_user.id, limit)
    return history

@app.get("/api/trade/logs")
async def get_bot_logs(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get bot activity logs"""
    logs = await trade_engine.get_bot_logs(current_user.id, limit)
    return {"logs": logs}

# ==================== MARKET DATA ====================

@app.get("/api/market/price/{exchange_id}/{symbol}")
async def get_price(exchange_id: str, symbol: str):
    """Get current price"""
    try:
        price = await exchange_service.get_ticker_price(exchange_id, symbol)
        return {"exchange": exchange_id, "symbol": symbol, "price": price}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/market/price-history/{symbol}")
async def get_price_history(
    symbol: str,
    interval: str = "1m",
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get price history for chart"""
    try:
        # Get first connected exchange
        exchange_conn = db.query(ExchangeConnection).filter(
            ExchangeConnection.user_id == current_user.id,
            ExchangeConnection.is_active == True
        ).first()
        
        if not exchange_conn:
            raise HTTPException(status_code=400, detail="No exchange connected")
        
        history = await exchange_service.get_price_history(
            symbol, interval, limit, exchange_conn.exchange_id
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/market/top-coins")
async def get_top_coins(limit: int = 10):
    """Get top coins by volume"""
    coins = await exchange_service.get_top_coins(limit)
    return coins

# ==================== ANALYTICS ====================

@app.get("/api/analytics/pnl")
async def get_pnl(
    period: str = "24h",
    current_user: User = Depends(get_current_user)
):
    """Get PnL data"""
    pnl_data = await trade_engine.get_pnl_data(current_user.id, period)
    return pnl_data

@app.get("/api/analytics/statistics")
async def get_statistics(current_user: User = Depends(get_current_user)):
    """Get trading statistics"""
    stats = await trade_engine.get_statistics(current_user.id)
    return stats

# ==================== WEBSOCKET ====================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket for real-time updates"""
    await manager.connect(user_id, websocket)
    try:
        while True:
            # Receive from client
            data = await websocket.receive_text()
            
            # Send updates
            updates = await trade_engine.get_live_updates(user_id)
            await websocket.send_json(updates)
            
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(user_id)

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "database": "connected" if check_db_connection() else "disconnected"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AutoFutures API v2.0", "docs": "/docs"}

# ==================== RUN ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
