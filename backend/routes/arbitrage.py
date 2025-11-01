# backend/routes/arbitrage.py
# ДОБАВЬТЕ ЭТИ ENDPOINTS В main.py

from fastapi import APIRouter, Depends
from services.arbitrage_analyzer import ArbitrageAnalyzer
from database.models import User
# ... другие импорты из main.py

# Создайте роутер (добавьте в main.py после создания app)
# arbitrage_analyzer = ArbitrageAnalyzer(exchange_service)

# ==================== ARBITRAGE ANALYSIS ENDPOINTS ====================

@app.post("/api/arbitrage/analyze")
async def analyze_arbitrage_opportunity(
    coin: str,
    exchange_from: str,
    exchange_to: str,
    order_size: float = 100,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze specific arbitrage opportunity
    Returns detailed breakdown with profitability score
    """
    try:
        from services.arbitrage_analyzer import ArbitrageAnalyzer
        analyzer = ArbitrageAnalyzer(exchange_service)
        
        result = await analyzer.analyze_opportunity(
            current_user.id,
            coin,
            exchange_from,
            exchange_to,
            order_size
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/arbitrage/scan")
async def scan_arbitrage_opportunities(
    coins: List[str],
    exchanges: List[str],
    min_profit_percent: float = 0.5,
    order_size: float = 100,
    current_user: User = Depends(get_current_user)
):
    """
    Scan multiple coins and exchanges for best opportunities
    Returns top 10 sorted by profitability
    """
    try:
        from services.arbitrage_analyzer import ArbitrageAnalyzer
        analyzer = ArbitrageAnalyzer(exchange_service)
        
        opportunities = await analyzer.find_best_opportunities(
            current_user.id,
            coins,
            exchanges,
            min_profit_percent,
            order_size
        )
        
        return {
            "success": True,
            "count": len(opportunities),
            "opportunities": opportunities
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/exchanges/supported")
async def get_supported_exchanges():
    """Get list of all supported exchanges with details"""
    from utils.exchange_config import get_supported_exchanges
    
    exchanges = get_supported_exchanges()
    
    # Format for frontend
    result = []
    for exchange_id, config in exchanges.items():
        result.append({
            "id": exchange_id,
            "name": config['name'],
            "tier": config['tier'],
            "has_spot": config['has']['spot'],
            "has_futures": config['has']['futures'],
            "maker_fee": config['fees']['maker'],
            "taker_fee": config['fees']['taker']
        })
    
    return {
        "exchanges": sorted(result, key=lambda x: x['tier']),
        "total": len(result)
    }

@app.get("/api/exchanges/{exchange_id}/network-status/{coin}")
async def check_network_status(
    exchange_id: str,
    coin: str,
    current_user: User = Depends(get_current_user)
):
    """Check if deposits/withdrawals are enabled for coin"""
    try:
        from services.arbitrage_analyzer import ArbitrageAnalyzer
        analyzer = ArbitrageAnalyzer(exchange_service)
        
        status = await analyzer._check_network_status(coin, [exchange_id])
        
        return {
            "exchange": exchange_id,
            "coin": coin,
            "status": status.get(exchange_id, {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
