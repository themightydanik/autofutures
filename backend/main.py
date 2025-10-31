# backend/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict
import asyncio
import json
from datetime import datetime
import uvicorn

# Import custom modules
from services.exchange_service import ExchangeService
from services.trade_engine import TradeEngine
from services.user_service import UserService
from models.schemas import (
    UserLogin, UserRegister, UserSettings, TradeParams, 
    TradeStatus, Balance, BotLog, ActiveTrade
)

app = FastAPI(title="AutoFutures API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Services initialization
user_service = UserService()
exchange_service = ExchangeService()
trade_engine = TradeEngine(exchange_service)

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# ==================== AUTH ENDPOINTS ====================

@app.post("/api/auth/register")
async def register(user: UserRegister):
    """Регистрация нового пользователя"""
    try:
        result = await user_service.register_user(user.username, user.password)
        return {"success": True, "token": result["token"], "user_id": result["user_id"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
async def login(user: UserLogin):
    """Авторизация пользователя"""
    try:
        result = await user_service.login_user(user.username, user.password)
        return {"success": True, "token": result["token"], "user_id": result["user_id"]}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# ==================== USER SETTINGS ====================

@app.get("/api/user/settings")
async def get_settings(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получить настройки пользователя"""
    user_id = await user_service.verify_token(credentials.credentials)
    settings = await user_service.get_user_settings(user_id)
    return settings

@app.post("/api/user/settings")
async def save_settings(settings: UserSettings, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Сохранить настройки пользователя"""
    user_id = await user_service.verify_token(credentials.credentials)
    await user_service.save_user_settings(user_id, settings.dict())
    return {"success": True}

# ==================== EXCHANGE ENDPOINTS ====================

@app.post("/api/exchanges/connect")
async def connect_exchange(
    exchange_id: str,
    api_key: str,
    secret_key: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Подключить биржу по API ключам"""
    user_id = await user_service.verify_token(credentials.credentials)
    try:
        result = await exchange_service.connect_exchange(
            user_id, exchange_id, api_key, secret_key
        )
        return {"success": True, "message": f"Connected to {exchange_id}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/exchanges/balances")
async def get_balances(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получить балансы на всех подключенных биржах"""
    user_id = await user_service.verify_token(credentials.credentials)
    balances = await exchange_service.get_all_balances(user_id)
    return balances

@app.get("/api/exchanges/{exchange_id}/price/{symbol}")
async def get_price(exchange_id: str, symbol: str):
    """Получить текущую цену монеты на бирже"""
    price = await exchange_service.get_ticker_price(exchange_id, symbol)
    return {"exchange": exchange_id, "symbol": symbol, "price": price}

# ==================== TRADING ENDPOINTS ====================

@app.post("/api/trade/start")
async def start_trading(
    params: TradeParams,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Запустить торгового бота"""
    user_id = await user_service.verify_token(credentials.credentials)
    
    # Получаем настройки пользователя
    settings = await user_service.get_user_settings(user_id)
    
    # Запускаем торговый движок
    await trade_engine.start_trading(user_id, settings, params.dict())
    
    # Отправляем уведомление через WebSocket
    await manager.broadcast({
        "type": "trade_status",
        "status": "started",
        "message": "Бот запущен! Начинаю мониторинг рынка..."
    })
    
    return {"success": True, "status": "started"}

@app.post("/api/trade/stop")
async def stop_trading(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Остановить торгового бота"""
    user_id = await user_service.verify_token(credentials.credentials)
    await trade_engine.stop_trading(user_id)
    
    await manager.broadcast({
        "type": "trade_status",
        "status": "stopped",
        "message": "Бот остановлен"
    })
    
    return {"success": True, "status": "stopped"}

@app.get("/api/trade/status")
async def get_trade_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получить текущий статус торговли"""
    user_id = await user_service.verify_token(credentials.credentials)
    status = await trade_engine.get_status(user_id)
    return status

@app.put("/api/trade/parameters")
async def update_parameters(
    params: TradeParams,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Обновить параметры торговли на лету"""
    user_id = await user_service.verify_token(credentials.credentials)
    await trade_engine.update_parameters(user_id, params.dict())
    return {"success": True}

@app.get("/api/trade/active")
async def get_active_trades(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получить список активных сделок"""
    user_id = await user_service.verify_token(credentials.credentials)
    trades = await trade_engine.get_active_trades(user_id)
    return trades

@app.get("/api/trade/history")
async def get_trade_history(
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получить историю сделок"""
    user_id = await user_service.verify_token(credentials.credentials)
    history = await trade_engine.get_trade_history(user_id, limit)
    return history

# ==================== ANALYTICS ENDPOINTS ====================

@app.get("/api/analytics/pnl")
async def get_pnl(
    period: str = "24h",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получить данные PnL за период"""
    user_id = await user_service.verify_token(credentials.credentials)
    pnl_data = await trade_engine.get_pnl_data(user_id, period)
    return pnl_data

@app.get("/api/analytics/statistics")
async def get_statistics(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получить статистику торговли"""
    user_id = await user_service.verify_token(credentials.credentials)
    stats = await trade_engine.get_statistics(user_id)
    return stats

# ==================== MARKET DATA ====================

@app.get("/api/market/price-history/{symbol}")
async def get_price_history(symbol: str, interval: str = "1m", limit: int = 100):
    """Получить историю цен для графика"""
    history = await exchange_service.get_price_history(symbol, interval, limit)
    return history

@app.get("/api/market/top-coins")
async def get_top_coins(limit: int = 10):
    """Получить топ монет по объёму торгов"""
    coins = await exchange_service.get_top_coins(limit)
    return coins

# ==================== WEBSOCKET ====================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket для обновлений в реальном времени"""
    await manager.connect(websocket)
    try:
        while True:
            # Получаем сообщения от клиента
            data = await websocket.receive_text()
            
            # Обрабатываем подписки на события
            message = json.loads(data)
            if message.get("type") == "subscribe":
                # Подписка на обновления для конкретного пользователя
                pass
            
            # Отправляем обновления
            updates = await trade_engine.get_live_updates(user_id)
            await websocket.send_json(updates)
            
            await asyncio.sleep(1)  # Обновления каждую секунду
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Проверка работоспособности API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# ==================== RUN ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
