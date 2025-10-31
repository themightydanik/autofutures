# backend/services/trade_engine.py
import asyncio
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from services.exchange_service import ExchangeService
from models.schemas import TradeStatus, TradeSide, LogType

logger = logging.getLogger(__name__)

class TradeEngine:
    """Основной торговый движок для автоматизированной торговли"""
    
    def __init__(self, exchange_service: ExchangeService):
        self.exchange_service = exchange_service
        self.active_bots: Dict[str, bool] = {}  # {user_id: is_running}
        self.bot_tasks: Dict[str, asyncio.Task] = {}  # {user_id: task}
        self.user_settings: Dict[str, Dict] = {}  # {user_id: settings}
        self.trade_params: Dict[str, Dict] = {}  # {user_id: params}
        self.active_trades: Dict[str, List[Dict]] = defaultdict(list)  # {user_id: [trades]}
        self.trade_history: Dict[str, List[Dict]] = defaultdict(list)  # {user_id: [completed_trades]}
        self.bot_logs: Dict[str, List[Dict]] = defaultdict(list)  # {user_id: [logs]}
        self.pnl_data: Dict[str, Dict] = {}  # {user_id: {total_pnl, pnl_percent}}
    
    async def start_trading(self, user_id: str, settings: Dict, params: Dict):
        """Запустить торгового бота"""
        try:
            if user_id in self.active_bots and self.active_bots[user_id]:
                raise ValueError("Bot is already running")
            
            self.user_settings[user_id] = settings
            self.trade_params[user_id] = params
            self.active_bots[user_id] = True
            
            # Инициализируем PnL
            if user_id not in self.pnl_data:
                self.pnl_data[user_id] = {
                    'total_pnl': 0.0,
                    'pnl_percent': 0.0,
                    'trades_count': 0,
                    'start_time': datetime.now()
                }
            
            # Логируем старт
            await self._add_log(user_id, LogType.SUCCESS, "🚀 Бот запущен! Начинаю мониторинг рынка...")
            
            # Запускаем торговый цикл
            if settings['trade_type'] == 'arbitrage':
                task = asyncio.create_task(self._arbitrage_loop(user_id))
            else:
                task = asyncio.create_task(self._margin_trading_loop(user_id))
            
            self.bot_tasks[user_id] = task
            logger.info(f"Trading bot started for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error starting trading bot: {str(e)}")
            raise
    
    async def stop_trading(self, user_id: str):
        """Остановить торгового бота"""
        try:
            if user_id in self.active_bots:
                self.active_bots[user_id] = False
                
                # Отменяем задачу
                if user_id in self.bot_tasks:
                    self.bot_tasks[user_id].cancel()
                    try:
                        await self.bot_tasks[user_id]
                    except asyncio.CancelledError:
                        pass
                    del self.bot_tasks[user_id]
                
                await self._add_log(user_id, LogType.INFO, "⏸️ Бот остановлен. Открытые позиции сохранены.")
                logger.info(f"Trading bot stopped for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error stopping trading bot: {str(e)}")
            raise
    
    async def _arbitrage_loop(self, user_id: str):
        """Основной цикл арбитражной торговли"""
        await self._add_log(user_id, LogType.SEARCH, "🔍 Начинаю поиск возможностей арбитража...")
        
        while self.active_bots.get(user_id, False):
            try:
                params = self.trade_params[user_id]
                settings = self.user_settings[user_id]
                coin = params.get('coin', 'BTC')
                
                # Ищем возможности арбитража
                await self._add_log(user_id, LogType.SEARCH, f"📊 Анализирую спреды на {coin}/USDT между биржами...")
                
                opportunities = await self.exchange_service.find_arbitrage_opportunities(
                    user_id, 
                    coin, 
                    params.get('min_profit_threshold', 0.3)
                )
                
                if opportunities:
                    best_opp = opportunities[0]
                    spread = best_opp['spread_percent']
                    
                    await self._add_log(
                        user_id, 
                        LogType.SUCCESS, 
                        f"✅ Обнаружена возможность! Спред: {spread:.2f}% ({best_opp['buy_exchange']} → {best_opp['sell_exchange']})"
                    )
                    
                    # Выполняем арбитражную сделку
                    await self._execute_arbitrage(user_id, best_opp, params)
                    
                else:
                    await self._add_log(user_id, LogType.SEARCH, "⏳ Спред недостаточен, продолжаю мониторинг...")
                
                # Задержка в зависимости от частоты
                frequency_delays = {'low': 30, 'medium': 15, 'high': 5}
                delay = frequency_delays.get(params.get('frequency', 'medium'), 15)
                await asyncio.sleep(delay)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in arbitrage loop: {str(e)}")
                await self._add_log(user_id, LogType.ERROR, f"❌ Ошибка: {str(e)}")
                await asyncio.sleep(10)
    
    async def _execute_arbitrage(self, user_id: str, opportunity: Dict, params: Dict):
        """Выполнить арбитражную сделку"""
        try:
            coin = opportunity['coin']
            buy_exchange = opportunity['buy_exchange']
            sell_exchange = opportunity['sell_exchange']
            buy_price = opportunity['buy_price']
            sell_price = opportunity['sell_price']
            
            # Рассчитываем количество монет
            order_size_usd = params.get('order_size', 100)
            amount = order_size_usd / buy_price
            
            trade_id = str(uuid.uuid4())
            
            # Создаём запись об активной сделке
            active_trade = {
                'id': trade_id,
                'user_id': user_id,
                'coin': coin,
                'trade_type': 'Арбитраж',
                'entry_price': buy_price,
                'current_price': buy_price,
                'amount': amount,
                'pnl': 0.0,
                'pnl_percent': 0.0,
                'status': 'active',
                'exchanges': [buy_exchange, sell_exchange],
                'opened_at': datetime.now(),
                'updated_at': datetime.now()
            }
            self.active_trades[user_id].append(active_trade)
            
            # ШАГ 1: Покупка на первой бирже
            await self._add_log(
                user_id, 
                LogType.BUY, 
                f"💰 Покупаю {amount:.4f} {coin} на {buy_exchange} по ${buy_price:.2f}"
            )
            
            try:
                # buy_order = await self.exchange_service.create_market_order(
                #     user_id, buy_exchange, coin, 'buy', amount
                # )
                await asyncio.sleep(2)  # Симуляция выполнения ордера
            except Exception as e:
                await self._add_log(user_id, LogType.ERROR, f"❌ Ошибка при покупке: {str(e)}")
                self.active_trades[user_id].remove(active_trade)
                return
            
            # ШАГ 2: Перевод между биржами (если нужно)
            await self._add_log(
                user_id, 
                LogType.TRANSFER, 
                f"📤 Перевожу {amount:.4f} {coin}: {buy_exchange} → {sell_exchange}"
            )
            await asyncio.sleep(3)  # Симуляция перевода
            
            # ШАГ 3: Продажа на второй бирже
            await self._add_log(
                user_id, 
                LogType.SELL, 
                f"💸 Продаю {amount:.4f} {coin} на {sell_exchange} по ${sell_price:.2f}"
            )
            
            try:
                # sell_order = await self.exchange_service.create_market_order(
                #     user_id, sell_exchange, coin, 'sell', amount
                # )
                await asyncio.sleep(2)  # Симуляция выполнения ордера
            except Exception as e:
                await self._add_log(user_id, LogType.ERROR, f"❌ Ошибка при продаже: {str(e)}")
                return
            
            # Рассчитываем профит
            profit_usd = (sell_price - buy_price) * amount
            profit_percent = ((sell_price - buy_price) / buy_price) * 100
            
            # Обновляем PnL
            self.pnl_data[user_id]['total_pnl'] += profit_usd
            self.pnl_data[user_id]['trades_count'] += 1
            
            # Завершаем сделку
            completed_trade = {
                **active_trade,
                'exit_price': sell_price,
                'pnl': profit_usd,
                'pnl_percent': profit_percent,
                'status': 'completed',
                'closed_at': datetime.now()
            }
            
            self.active_trades[user_id].remove(active_trade)
            self.trade_history[user_id].append(completed_trade)
            
            await self._add_log(
                user_id, 
                LogType.PROFIT, 
                f"🎉 Сделка завершена! Профит: +${profit_usd:.2f} ({profit_percent:.2f}%)"
            )
            
            logger.info(f"Arbitrage trade completed: ${profit_usd:.2f}")
            
        except Exception as e:
            logger.error(f"Error executing arbitrage: {str(e)}")
            await self._add_log(user_id, LogType.ERROR, f"❌ Ошибка выполнения сделки: {str(e)}")
    
    async def _margin_trading_loop(self, user_id: str):
        """Основной цикл маржинальной торговли"""
        await self._add_log(user_id, LogType.SEARCH, "🔍 Начинаю анализ рынка для маржинальной торговли...")
        
        while self.active_bots.get(user_id, False):
            try:
                params = self.trade_params[user_id]
                settings = self.user_settings[user_id]
                coin = params.get('coin', 'BTC')
                
                await self._add_log(user_id, LogType.SEARCH, f"📈 Анализирую графики {coin}/USDT...")
                
                # Здесь должна быть логика анализа и определения точки входа
                # В зависимости от выбранной стратегии
                strategy = settings.get('strategy')
                
                # Симуляция поиска точки входа
                await asyncio.sleep(10)
                
                # Случайно определяем, нашли ли мы точку входа
                import random
                if random.random() > 0.7:
                    await self._add_log(user_id, LogType.SUCCESS, "✅ Обнаружена точка входа!")
                    await self._execute_margin_trade(user_id, params)
                else:
                    await self._add_log(user_id, LogType.SEARCH, "⏳ Жду подходящих условий для входа...")
                
                # Задержка
                frequency_delays = {'low': 60, 'medium': 30, 'high': 10}
                delay = frequency_delays.get(params.get('frequency', 'medium'), 30)
                await asyncio.sleep(delay)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in margin trading loop: {str(e)}")
                await asyncio.sleep(10)
    
    async def _execute_margin_trade(self, user_id: str, params: Dict):
        """Выполнить маржинальную сделку"""
        # Здесь логика открытия и закрытия позиций для маржинальной торговли
        # Аналогично арбитражу, но с использованием только одной биржи
        pass
    
    async def _add_log(self, user_id: str, log_type: LogType, message: str):
        """Добавить запись в лог бота"""
        log = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'timestamp': datetime.now(),
            'time': datetime.now().strftime('%H:%M:%S'),
            'log_type': log_type.value if isinstance(log_type, LogType) else log_type,
            'type': log_type.value if isinstance(log_type, LogType) else log_type,
            'message': message,
            'status': 'active' if log_type == LogType.SEARCH else 'completed'
        }
        self.bot_logs[user_id].insert(0, log)
        
        # Ограничиваем количество логов
        if len(self.bot_logs[user_id]) > 100:
            self.bot_logs[user_id] = self.bot_logs[user_id][:100]
    
    async def get_status(self, user_id: str) -> Dict:
        """Получить статус торговли"""
        return {
            'is_running': self.active_bots.get(user_id, False),
            'active_trades_count': len(self.active_trades.get(user_id, [])),
            'total_trades': self.pnl_data.get(user_id, {}).get('trades_count', 0),
            'total_pnl': self.pnl_data.get(user_id, {}).get('total_pnl', 0),
            'pnl_percent': self.pnl_data.get(user_id, {}).get('pnl_percent', 0)
        }
    
    async def update_parameters(self, user_id: str, params: Dict):
        """Обновить параметры торговли"""
        self.trade_params[user_id] = params
        await self._add_log(user_id, LogType.INFO, "⚙️ Параметры торговли обновлены")
    
    async def get_active_trades(self, user_id: str) -> List[Dict]:
        """Получить активные сделки"""
        return self.active_trades.get(user_id, [])
    
    async def get_trade_history(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Получить историю сделок"""
        history = self.trade_history.get(user_id, [])
        return history[:limit]
    
    async def get_pnl_data(self, user_id: str, period: str = "24h") -> Dict:
        """Получить данные PnL"""
        # Генерируем данные для графика
        pnl_chart = []
        now = datetime.now()
        
        for i in range(24):
            pnl_chart.append({
                'timestamp': (now - timedelta(hours=23-i)).isoformat(),
                'time': f"{i}:00",
                'pnl': self.pnl_data.get(user_id, {}).get('total_pnl', 0) * (i + 1) / 24,
                'pnl_percent': self.pnl_data.get(user_id, {}).get('pnl_percent', 0) * (i + 1) / 24
            })
        
        return {
            'chart_data': pnl_chart,
            'total_pnl': self.pnl_data.get(user_id, {}).get('total_pnl', 0),
            'pnl_percent': self.pnl_data.get(user_id, {}).get('pnl_percent', 0)
        }
    
    async def get_statistics(self, user_id: str) -> Dict:
        """Получить статистику торговли"""
        history = self.trade_history.get(user_id, [])
        
        if not history:
            return {
                'total_trades': 0,
                'successful_trades': 0,
                'failed_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'trades_today': 0
            }
        
        successful_trades = [t for t in history if t.get('pnl', 0) > 0]
        failed_trades = [t for t in history if t.get('pnl', 0) < 0]
        
        today = datetime.now().date()
        trades_today = [t for t in history if t.get('closed_at', datetime.now()).date() == today]
        
        return {
            'total_trades': len(history),
            'successful_trades': len(successful_trades),
            'failed_trades': len(failed_trades),
            'win_rate': (len(successful_trades) / len(history) * 100) if history else 0,
            'total_pnl': sum(t.get('pnl', 0) for t in history),
            'best_trade': max((t.get('pnl', 0) for t in history), default=0),
            'worst_trade': min((t.get('pnl', 0) for t in history), default=0),
            'trades_today': len(trades_today),
            'pnl_today': sum(t.get('pnl', 0) for t in trades_today)
        }
    
    async def get_live_updates(self, user_id: str) -> Dict:
        """Получить обновления для WebSocket"""
        return {
            'type': 'update',
            'data': {
                'pnl': self.pnl_data.get(user_id, {}).get('total_pnl', 0),
                'pnl_percent': self.pnl_data.get(user_id, {}).get('pnl_percent', 0),
                'active_trades': self.active_trades.get(user_id, []),
                'latest_logs': self.bot_logs.get(user_id, [])[:10],
                'is_running': self.active_bots.get(user_id, False)
            },
            'timestamp': datetime.now().isoformat()
        }
