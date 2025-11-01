# backend/services/exchange_service.py (REAL VERSION)
import ccxt
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ExchangeService:
    """Real exchange service with CCXT"""
    
    def __init__(self):
        self.exchanges: Dict[str, Dict[str, ccxt.Exchange]] = {}
        self.supported_exchanges = {
            'binance': ccxt.binance,
            'gateio': ccxt.gateio,
            'bybit': ccxt.bybit,
        }
    
    async def connect_exchange(self, user_id: str, exchange_id: str, api_key: str, secret_key: str) -> bool:
        """Connect to exchange with API keys"""
        try:
            if exchange_id not in self.supported_exchanges:
                raise ValueError(f"Exchange {exchange_id} not supported")
            
            exchange_class = self.supported_exchanges[exchange_id]
            exchange = exchange_class({
                'apiKey': api_key,
                'secret': secret_key,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            
            # Test connection
            await exchange.load_markets()
            balance = await exchange.fetch_balance()
            
            # Save connection
            if user_id not in self.exchanges:
                self.exchanges[user_id] = {}
            self.exchanges[user_id][exchange_id] = exchange
            
            logger.info(f"Connected to {exchange_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {exchange_id}: {str(e)}")
            raise Exception(f"Connection failed: {str(e)}")
    
    async def get_balance(self, user_id: str, exchange_id: str) -> Dict:
        """Get balance on exchange"""
        try:
            exchange = self._get_exchange(user_id, exchange_id)
            balance = await exchange.fetch_balance()
            
            usdt_balance = balance.get('USDT', {})
            return {
                'exchange': exchange_id,
                'currency': 'USDT',
                'free': usdt_balance.get('free', 0),
                'locked': usdt_balance.get('used', 0),
                'total': usdt_balance.get('total', 0),
                'updated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching balance: {str(e)}")
            return {'exchange': exchange_id, 'currency': 'USDT', 'free': 0, 'locked': 0, 'total': 0}
    
    async def get_all_balances(self, user_id: str) -> List[Dict]:
        """Get balances on all exchanges"""
        balances = []
        if user_id in self.exchanges:
            for exchange_id in self.exchanges[user_id].keys():
                balance = await self.get_balance(user_id, exchange_id)
                balances.append(balance)
        return balances
    
    async def get_ticker_price(self, exchange_id: str, symbol: str) -> float:
        """Get current price"""
        try:
            exchange_class = self.supported_exchanges[exchange_id]
            exchange = exchange_class({'enableRateLimit': True})
            ticker = await exchange.fetch_ticker(f"{symbol}/USDT")
            return ticker['last']
        except Exception as e:
            logger.error(f"Error fetching price: {str(e)}")
            raise
    
    async def get_price_history(self, symbol: str, interval: str = '1m', limit: int = 100, exchange_id: str = 'binance') -> List[Dict]:
        """Get price history for chart"""
        try:
            exchange = ccxt.binance({'enableRateLimit': True})
            ohlcv = await exchange.fetch_ohlcv(f"{symbol}/USDT", timeframe=interval, limit=limit)
            
            history = []
            for candle in ohlcv:
                history.append({
                    'timestamp': candle[0],
                    'time': datetime.fromtimestamp(candle[0] / 1000).strftime('%H:%M'),
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'price': candle[4],
                    'volume': candle[5]
                })
            
            return history
        except Exception as e:
            logger.error(f"Error fetching history: {str(e)}")
            return []
    
    async def get_available_pairs(self, user_id: str, exchange_id: str) -> List[str]:
        """Get available trading pairs"""
        try:
            exchange = self._get_exchange(user_id, exchange_id)
            markets = await exchange.load_markets()
            pairs = [symbol for symbol in markets.keys() if '/USDT' in symbol and ':USDT' not in symbol]
            return sorted(pairs)[:100]  # Return top 100
        except Exception as e:
            logger.error(f"Error fetching pairs: {str(e)}")
            return []
    
    async def get_top_coins(self, limit: int = 10) -> List[Dict]:
        """Get top coins by volume"""
        try:
            exchange = ccxt.binance({'enableRateLimit': True})
            tickers = await exchange.fetch_tickers()
            
            usdt_pairs = {k: v for k, v in tickers.items() if '/USDT' in k and ':USDT' not in k}
            sorted_pairs = sorted(usdt_pairs.items(), key=lambda x: x[1].get('quoteVolume', 0), reverse=True)[:limit]
            
            coins = []
            for symbol, ticker in sorted_pairs:
                coin_symbol = symbol.split('/')[0]
                coins.append({
                    'symbol': coin_symbol,
                    'name': coin_symbol,
                    'price': ticker.get('last', 0),
                    'change': ticker.get('percentage', 0),
                    'volume': ticker.get('quoteVolume', 0)
                })
            
            return coins
        except Exception as e:
            logger.error(f"Error fetching top coins: {str(e)}")
            return []
    
    async def create_market_order(self, user_id: str, exchange_id: str, symbol: str, side: str, amount: float) -> Dict:
        """Create market order"""
        try:
            exchange = self._get_exchange(user_id, exchange_id)
            order = await exchange.create_order(
                symbol=f"{symbol}/USDT",
                type='market',
                side=side.lower(),
                amount=amount
            )
            logger.info(f"Created {side} order: {amount} {symbol} on {exchange_id}")
            return order
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            raise
    
    async def find_arbitrage_opportunities(self, user_id: str, symbol: str, min_profit: float = 0.5) -> List[Dict]:
        """Find arbitrage opportunities"""
        opportunities = []
        if user_id not in self.exchanges or len(self.exchanges[user_id]) < 2:
            return opportunities
        
        try:
            prices = {}
            for exchange_id, exchange in self.exchanges[user_id].items():
                try:
                    ticker = await exchange.fetch_ticker(f"{symbol}/USDT")
                    prices[exchange_id] = {'bid': ticker['bid'], 'ask': ticker['ask']}
                except:
                    continue
            
            exchange_ids = list(prices.keys())
            for i in range(len(exchange_ids)):
                for j in range(i + 1, len(exchange_ids)):
                    buy_ex = exchange_ids[i]
                    sell_ex = exchange_ids[j]
                    
                    buy_price = prices[buy_ex]['ask']
                    sell_price = prices[sell_ex]['bid']
                    spread = ((sell_price - buy_price) / buy_price) * 100
                    
                    if spread > min_profit:
                        opportunities.append({
                            'coin': symbol,
                            'buy_exchange': buy_ex,
                            'sell_exchange': sell_ex,
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'spread_percent': spread,
                            'timestamp': datetime.now().isoformat()
                        })
            
            return sorted(opportunities, key=lambda x: x['spread_percent'], reverse=True)
        except Exception as e:
            logger.error(f"Error finding arbitrage: {str(e)}")
            return []
    
    def _get_exchange(self, user_id: str, exchange_id: str) -> ccxt.Exchange:
        """Get exchange instance"""
        if user_id not in self.exchanges or exchange_id not in self.exchanges[user_id]:
            raise ValueError(f"Exchange {exchange_id} not connected")
        return self.exchanges[user_id][exchange_id]
    
    async def close_all_connections(self, user_id: str):
        """Close all connections"""
        if user_id in self.exchanges:
            for exchange in self.exchanges[user_id].values():
                await exchange.close()
            del self.exchanges[user_id]
