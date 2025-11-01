# backend/services/arbitrage_scanner.py
"""
Real-time arbitrage opportunity scanner
Continuously monitors prices across exchanges to find profitable spreads
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from collections import defaultdict
from utils.exchange_config import get_exchange_config, get_supported_exchanges

logger = logging.getLogger(__name__)

class ArbitrageScanner:
    """
    Real-time scanner for arbitrage opportunities
    Monitors prices across multiple exchanges simultaneously
    """
    
    def __init__(self, exchange_service):
        self.exchange_service = exchange_service
        self.active_scans = {}  # {user_id: scan_task}
        self.opportunities_cache = defaultdict(list)  # {user_id: [opportunities]}
        self.price_cache = {}  # Cache for latest prices
        self.scan_interval = 3  # seconds between scans
    
    async def start_scanning(
        self,
        user_id: str,
        coins: List[str],
        exchanges: List[str],
        min_spread_percent: float = 0.5,
        order_size: float = 100,
        check_network: bool = True
    ):
        """
        Start continuous scanning for arbitrage opportunities
        """
        if user_id in self.active_scans:
            logger.info(f"Scanner already running for user {user_id}")
            return
        
        # Create scan task
        task = asyncio.create_task(
            self._scan_loop(
                user_id, coins, exchanges, 
                min_spread_percent, order_size, check_network
            )
        )
        
        self.active_scans[user_id] = {
            'task': task,
            'started_at': datetime.now(),
            'coins': coins,
            'exchanges': exchanges,
            'min_spread': min_spread_percent
        }
        
        logger.info(f"Scanner started for user {user_id}")
    
    async def stop_scanning(self, user_id: str):
        """Stop scanning for user"""
        if user_id in self.active_scans:
            self.active_scans[user_id]['task'].cancel()
            del self.active_scans[user_id]
            logger.info(f"Scanner stopped for user {user_id}")
    
    def get_opportunities(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get latest opportunities found for user"""
        opportunities = self.opportunities_cache.get(user_id, [])
        # Sort by profitability
        sorted_opps = sorted(
            opportunities, 
            key=lambda x: x.get('net_profit_percent', 0), 
            reverse=True
        )
        return sorted_opps[:limit]
    
    def get_scan_status(self, user_id: str) -> Dict:
        """Get current scan status"""
        if user_id not in self.active_scans:
            return {'is_scanning': False}
        
        scan_info = self.active_scans[user_id]
        opportunities = self.opportunities_cache.get(user_id, [])
        
        # Calculate stats
        profitable_count = len([o for o in opportunities if o['net_profit_percent'] > 0])
        best_opp = max(opportunities, key=lambda x: x['net_profit_percent']) if opportunities else None
        
        return {
            'is_scanning': True,
            'started_at': scan_info['started_at'].isoformat(),
            'uptime_seconds': (datetime.now() - scan_info['started_at']).seconds,
            'coins': scan_info['coins'],
            'exchanges': scan_info['exchanges'],
            'min_spread': scan_info['min_spread'],
            'total_opportunities': len(opportunities),
            'profitable_opportunities': profitable_count,
            'best_opportunity': {
                'coin': best_opp['coin'],
                'spread': best_opp['net_profit_percent'],
                'exchanges': f"{best_opp['buy_exchange']} → {best_opp['sell_exchange']}"
            } if best_opp else None
        }
    
    async def _scan_loop(
        self,
        user_id: str,
        coins: List[str],
        exchanges: List[str],
        min_spread: float,
        order_size: float,
        check_network: bool
    ):
        """Main scanning loop"""
        consecutive_errors = 0
        max_errors = 5
        
        while consecutive_errors < max_errors:
            try:
                # Get all prices in parallel
                prices = await self._fetch_all_prices(user_id, coins, exchanges)
                
                if not prices:
                    consecutive_errors += 1
                    await asyncio.sleep(self.scan_interval * 2)
                    continue
                
                # Find opportunities
                opportunities = await self._find_opportunities(
                    user_id, prices, exchanges, 
                    min_spread, order_size, check_network
                )
                
                # Update cache
                if opportunities:
                    self.opportunities_cache[user_id] = opportunities
                    logger.info(f"Found {len(opportunities)} opportunities for user {user_id}")
                
                consecutive_errors = 0  # Reset on success
                
                # Wait before next scan
                await asyncio.sleep(self.scan_interval)
                
            except asyncio.CancelledError:
                logger.info(f"Scan loop cancelled for user {user_id}")
                break
            except Exception as e:
                logger.error(f"Error in scan loop: {str(e)}")
                consecutive_errors += 1
                await asyncio.sleep(self.scan_interval * 2)
        
        if consecutive_errors >= max_errors:
            logger.error(f"Scanner stopped due to consecutive errors for user {user_id}")
            if user_id in self.active_scans:
                del self.active_scans[user_id]
    
    async def _fetch_all_prices(
        self,
        user_id: str,
        coins: List[str],
        exchanges: List[str]
    ) -> Dict:
        """
        Fetch prices for all coins from all exchanges in parallel
        Returns: {coin: {exchange: {bid, ask, last, volume}}}
        """
        prices = defaultdict(dict)
        
        # Create tasks for parallel execution
        tasks = []
        for coin in coins:
            for exchange_id in exchanges:
                task = self._fetch_single_price(user_id, exchange_id, coin)
                tasks.append((coin, exchange_id, task))
        
        # Execute all in parallel
        results = await asyncio.gather(*[t[2] for t in tasks], return_exceptions=True)
        
        # Process results
        for (coin, exchange_id, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.debug(f"Error fetching {coin} from {exchange_id}: {str(result)}")
                continue
            
            if result:
                prices[coin][exchange_id] = result
        
        return dict(prices)
    
    async def _fetch_single_price(self, user_id: str, exchange_id: str, coin: str) -> Optional[Dict]:
        """Fetch price for single coin from single exchange"""
        try:
            # Check if exchange is connected
            if user_id not in self.exchange_service.exchanges or \
               exchange_id not in self.exchange_service.exchanges.get(user_id, {}):
                # Use public API
                exchange_class = self.exchange_service.supported_exchanges.get(exchange_id)
                if not exchange_class:
                    return None
                
                exchange = exchange_class({'enableRateLimit': True})
                ticker = await exchange.fetch_ticker(f"{coin}/USDT")
            else:
                # Use user's connected exchange
                exchange = self.exchange_service._get_exchange(user_id, exchange_id)
                ticker = await exchange.fetch_ticker(f"{coin}/USDT")
            
            return {
                'bid': ticker.get('bid', 0),
                'ask': ticker.get('ask', 0),
                'last': ticker.get('last', 0),
                'volume': ticker.get('quoteVolume', 0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.debug(f"Error fetching {coin} from {exchange_id}: {str(e)}")
            return None
    
    async def _find_opportunities(
        self,
        user_id: str,
        prices: Dict,
        exchanges: List[str],
        min_spread: float,
        order_size: float,
        check_network: bool
    ) -> List[Dict]:
        """Find arbitrage opportunities from price data"""
        opportunities = []
        
        for coin, exchange_prices in prices.items():
            # Need at least 2 exchanges with prices
            if len(exchange_prices) < 2:
                continue
            
            # Check all exchange pairs
            exchange_list = list(exchange_prices.keys())
            for i, buy_exchange in enumerate(exchange_list):
                for sell_exchange in exchange_list[i+1:]:
                    # Calculate both directions
                    for direction in [
                        (buy_exchange, sell_exchange),
                        (sell_exchange, buy_exchange)
                    ]:
                        buy_ex, sell_ex = direction
                        
                        buy_price = exchange_prices[buy_ex]['ask']
                        sell_price = exchange_prices[sell_ex]['bid']
                        
                        if buy_price <= 0 or sell_price <= 0:
                            continue
                        
                        # Calculate spread
                        spread_percent = ((sell_price - buy_price) / buy_price) * 100
                        
                        if spread_percent < min_spread:
                            continue
                        
                        # Calculate fees and net profit
                        fees = self._calculate_fees(buy_ex, sell_ex, coin, order_size, buy_price)
                        net_profit = self._calculate_net_profit(
                            order_size, buy_price, sell_price, fees
                        )
                        
                        # Skip if not profitable after fees
                        if net_profit['profit_percent'] < 0:
                            continue
                        
                        # Check network status if required
                        if check_network:
                            network_ok = await self._quick_network_check(coin, [buy_ex, sell_ex])
                            if not network_ok:
                                continue
                        
                        # Calculate execution time
                        exec_time = self._estimate_execution_time(buy_ex, sell_ex)
                        
                        # Create opportunity record
                        opportunity = {
                            'coin': coin,
                            'buy_exchange': buy_ex,
                            'sell_exchange': sell_ex,
                            'buy_price': round(buy_price, 8),
                            'sell_price': round(sell_price, 8),
                            'raw_spread_percent': round(spread_percent, 3),
                            'net_profit_percent': round(net_profit['profit_percent'], 3),
                            'net_profit_usdt': round(net_profit['net_profit'], 2),
                            'total_fees': round(fees['total_fees'], 2),
                            'execution_time_seconds': exec_time,
                            'volume_buy': exchange_prices[buy_ex]['volume'],
                            'volume_sell': exchange_prices[sell_ex]['volume'],
                            'timestamp': datetime.now().isoformat(),
                            'status': 'active'
                        }
                        
                        opportunities.append(opportunity)
        
        return opportunities
    
    def _calculate_fees(
        self,
        buy_exchange: str,
        sell_exchange: str,
        coin: str,
        order_size: float,
        price: float
    ) -> Dict:
        """Calculate all fees"""
        buy_config = get_exchange_config(buy_exchange)
        sell_config = get_exchange_config(sell_exchange)
        
        if not buy_config or not sell_config:
            return {'total_fees': 0}
        
        # Trading fees
        buy_fee = (order_size * buy_config['fees']['taker']) / 100
        sell_fee = (order_size * sell_config['fees']['taker']) / 100
        
        # Withdrawal fee
        withdrawal_fee_crypto = buy_config['withdrawal_fees'].get(coin, 0)
        withdrawal_fee_usdt = withdrawal_fee_crypto * price
        
        # Network fee
        network_fee = 0.5
        
        total = buy_fee + sell_fee + withdrawal_fee_usdt + network_fee
        
        return {
            'buy_fee': buy_fee,
            'sell_fee': sell_fee,
            'withdrawal_fee': withdrawal_fee_usdt,
            'network_fee': network_fee,
            'total_fees': total
        }
    
    def _calculate_net_profit(
        self,
        order_size: float,
        buy_price: float,
        sell_price: float,
        fees: Dict
    ) -> Dict:
        """Calculate net profit"""
        gross_profit = ((sell_price - buy_price) / buy_price) * order_size
        net_profit = gross_profit - fees['total_fees']
        profit_percent = (net_profit / order_size) * 100
        
        return {
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'profit_percent': profit_percent,
            'is_profitable': net_profit > 0
        }
    
    def _estimate_execution_time(self, buy_exchange: str, sell_exchange: str) -> int:
        """Estimate execution time in seconds"""
        buy_config = get_exchange_config(buy_exchange)
        sell_config = get_exchange_config(sell_exchange)
        
        if not buy_config or not sell_config:
            return 600  # Default 10 minutes
        
        return (
            5 +  # Buy order
            buy_config['withdrawal_time'] +
            sell_config['deposit_time'] +
            5  # Sell order
        )
    
    async def _quick_network_check(self, coin: str, exchanges: List[str]) -> bool:
        """Quick check if network is enabled (cached)"""
        # In production, this should check real status from exchange API
        # For now, assume enabled for major coins
        major_coins = ['BTC', 'ETH', 'USDT', 'BNB', 'SOL']
        return coin in major_coins
    
    async def manual_scan(
        self,
        user_id: str,
        coins: List[str],
        exchanges: List[str],
        min_spread: float = 0.5,
        order_size: float = 100
    ) -> List[Dict]:
        """
        One-time manual scan (not continuous)
        Useful for "Scan Now" button
        """
        try:
            prices = await self._fetch_all_prices(user_id, coins, exchanges)
            
            if not prices:
                return []
            
            opportunities = await self._find_opportunities(
                user_id, prices, exchanges, 
                min_spread, order_size, check_network=True
            )
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error in manual scan: {str(e)}")
            return []

# Global instance
scanner = ArbitrageScanner(None)  # Will be initialized with exchange_service
