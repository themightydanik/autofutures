# backend/services/exchange_service.py
import ccxt
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ExchangeService:
    """Сервис для работы с криптобиржами через CCXT"""
    
    def __init__(self):
        self.exchanges: Dict[str, Dict[str, ccxt.Exchange]] = {}  # {user_id: {exchange_id: exchange_instance}}
        self.supported_exchanges = {
            'binance': ccxt.binance,
            'gateio': ccxt.gateio,
            'bybit': ccxt.bybit,
        }
    
    async def connect_exchange(self, user_id: str, exchange_id: str, api_key: str, secret_key: str) -> bool:
        """Подключение к бирже с API ключами"""
        try:
            if exchange_id not in self.supported_exchanges:
                raise ValueError(f"Exchange {exchange_id} not supported")
            
            exchange_class = self.supported_exchanges[exchange_id]
            exchange = exchange_class({
                'apiKey': api_key,
                'secret': secret_key,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',  # Для фьючерсов
                }
            })
            
            # Проверяем подключение
            await exchange.load_markets()
            balance = await exchange.fetch_balance()
            
            # Сохраняем подключение
            if user_id not in self.exchanges:
                self.exchanges[user_id] = {}
            self.exchanges[user_id][exchange_id] = exchange
            
            logger.info(f"Successfully connected to {exchange_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {exchange_id}: {str(e)}")
            raise Exception(f"Failed to connect to {exchange_id}: {str(e)}")
    
    async def get_balance(self, user_id: str, exchange_id: str) -> Dict:
        """Получить баланс на конкретной бирже"""
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
            logger.error(f"Error fetching balance from {exchange_id}: {str(e)}")
            return {
                'exchange': exchange_id,
                'currency': 'USDT',
                'free': 0,
                'locked': 0,
                'total': 0,
                'updated_at': datetime.now().isoformat()
            }
    
    async def get_all_balances(self, user_id: str) -> List[Dict]:
        """Получить балансы на всех подключенных биржах"""
        balances = []
        if user_id in self.exchanges:
            for exchange_id in self.exchanges[user_id].keys():
                balance = await self.get_balance(user_id, exchange_id)
                balances.append(balance)
        return balances
    
    async def get_ticker_price(self, exchange_id: str, symbol: str) -> float:
        """Получить текущую цену монеты"""
        try:
            # Используем публичное API (не требует авторизации)
            exchange_class = self.supported_exchanges[exchange_id]
            exchange = exchange_class({'enableRateLimit': True})
            
            ticker = await exchange.fetch_ticker(f"{symbol}/USDT")
            return ticker['last']
        except Exception as e:
            logger.error(f"Error fetching price for {symbol} from {exchange_id}: {str(e)}")
            raise
    
    async def get_orderbook(self, user_id: str, exchange_id: str, symbol: str) -> Dict:
        """Получить стакан ордеров"""
        try:
            exchange = self._get_exchange(user_id, exchange_id)
            orderbook = await exchange.fetch_order_book(f"{symbol}/USDT")
            return orderbook
        except Exception as e:
            logger.error(f"Error fetching orderbook: {str(e)}")
            raise
    
    async def create_market_order(self, user_id: str, exchange_id: str, symbol: str, side: str, amount: float) -> Dict:
        """Создать рыночный ордер"""
        try:
            exchange = self._get_exchange(user_id, exchange_id)
            order = await exchange.create_order(
                symbol=f"{symbol}/USDT",
                type='market',
                side=side.lower(),
                amount=amount
            )
            
            logger.info(f"Created {side} order for {amount} {symbol} on {exchange_id}")
            return order
            
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            raise
    
    async def create_limit_order(self, user_id: str, exchange_id: str, symbol: str, side: str, amount: float, price: float) -> Dict:
        """Создать лимитный ордер"""
        try:
            exchange = self._get_exchange(user_id, exchange_id)
            order = await exchange.create_order(
                symbol=f"{symbol}/USDT",
                type='limit',
                side=side.lower(),
                amount=amount,
                price=price
            )
            
            logger.info(f"Created limit {side} order for {amount} {symbol} at ${price} on {exchange_id}")
            return order
            
        except Exception as e:
            logger.error(f"Error creating limit order: {str(e)}")
            raise
    
    async def cancel_order(self, user_id: str, exchange_id: str, order_id: str, symbol: str) -> bool:
        """Отменить ордер"""
        try:
            exchange = self._get_exchange(user_id, exchange_id)
            await exchange.cancel_order(order_id, f"{symbol}/USDT")
            logger.info(f"Cancelled order {order_id} on {exchange_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return False
    
    async def get_open_orders(self, user_id: str, exchange_id: str, symbol: Optional[str] = None) -> List[Dict]:
        """Получить открытые ордера"""
        try:
            exchange = self._get_exchange(user_id, exchange_id)
            symbol_str = f"{symbol}/USDT" if symbol else None
            orders = await exchange.fetch_open_orders(symbol_str)
            return orders
        except Exception as e:
            logger.error(f"Error fetching open orders: {str(e)}")
            return []
    
    async def get_price_history(self, symbol: str, interval: str = '1m', limit: int = 100) -> List[Dict]:
        """Получить историю цен для графика"""
        try:
            # Используем Binance для исторических данных (самые полные данные)
            exchange = ccxt.binance({'enableRateLimit': True})
            
            # Преобразуем интервал в формат CCXT
            ohlcv = await exchange.fetch_ohlcv(
                f"{symbol}/USDT",
                timeframe=interval,
                limit=limit
            )
            
            # Форматируем данные
            history = []
            for candle in ohlcv:
                history.append({
                    'timestamp': candle[0],
                    'time': datetime.fromtimestamp(candle[0] / 1000).strftime('%H:%M'),
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'price': candle[4],  # Для простого графика
                    'volume': candle[5]
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error fetching price history: {str(e)}")
            return []
    
    async def get_top_coins(self, limit: int = 10) -> List[Dict]:
        """Получить топ монет по объёму"""
        try:
            exchange = ccxt.binance({'enableRateLimit': True})
            tickers = await exchange.fetch_tickers()
            
            # Фильтруем только USDT пары
            usdt_pairs = {k: v for k, v in tickers.items() if '/USDT' in k and ':USDT' not in k}
            
            # Сортируем по объёму
            sorted_pairs = sorted(
                usdt_pairs.items(),
                key=lambda x: x[1].get('quoteVolume', 0),
                reverse=True
            )[:limit]
            
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
    
    async def find_arbitrage_opportunities(self, user_id: str, symbol: str, min_profit: float = 0.5) -> List[Dict]:
        """Найти возможности для арбитража между биржами"""
        opportunities = []
        
        if user_id not in self.exchanges or len(self.exchanges[user_id]) < 2:
            return opportunities
        
        try:
            # Получаем цены на всех биржах пользователя
            prices = {}
            for exchange_id, exchange in self.exchanges[user_id].items():
                try:
                    ticker = await exchange.fetch_ticker(f"{symbol}/USDT")
                    prices[exchange_id] = {
                        'bid': ticker['bid'],  # Цена покупки
                        'ask': ticker['ask']   # Цена продажи
                    }
                except Exception as e:
                    logger.warning(f"Could not fetch price from {exchange_id}: {str(e)}")
                    continue
            
            # Ищем возможности арбитража
            exchange_ids = list(prices.keys())
            for i in range(len(exchange_ids)):
                for j in range(i + 1, len(exchange_ids)):
                    buy_exchange = exchange_ids[i]
                    sell_exchange = exchange_ids[j]
                    
                    # Покупаем на одной, продаём на другой
                    buy_price = prices[buy_exchange]['ask']
                    sell_price = prices[sell_exchange]['bid']
                    spread = ((sell_price - buy_price) / buy_price) * 100
                    
                    if spread > min_profit:
                        opportunities.append({
                            'coin': symbol,
                            'buy_exchange': buy_exchange,
                            'sell_exchange': sell_exchange,
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'spread_percent': spread,
                            'estimated_profit': spread,
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    # Проверяем обратное направление
                    buy_price = prices[sell_exchange]['ask']
                    sell_price = prices[buy_exchange]['bid']
                    spread = ((sell_price - buy_price) / buy_price) * 100
                    
                    if spread > min_profit:
                        opportunities.append({
                            'coin': symbol,
                            'buy_exchange': sell_exchange,
                            'sell_exchange': buy_exchange,
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'spread_percent': spread,
                            'estimated_profit': spread,
                            'timestamp': datetime.now().isoformat()
                        })
            
            return sorted(opportunities, key=lambda x: x['spread_percent'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error finding arbitrage opportunities: {str(e)}")
            return []
    
    def _get_exchange(self, user_id: str, exchange_id: str) -> ccxt.Exchange:
        """Получить инстанс биржи для пользователя"""
        if user_id not in self.exchanges or exchange_id not in self.exchanges[user_id]:
            raise ValueError(f"Exchange {exchange_id} not connected for user {user_id}")
        return self.exchanges[user_id][exchange_id]
    
    async def close_all_connections(self, user_id: str):
        """Закрыть все подключения к биржам для пользователя"""
        if user_id in self.exchanges:
            for exchange in self.exchanges[user_id].values():
                await exchange.close()
            del self.exchanges[user_id]
            logger.info(f"Closed all exchange connections for user {user_id}")
