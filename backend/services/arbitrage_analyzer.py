# backend/services/arbitrage_analyzer.py
"""
Advanced arbitrage analyzer with deposit/withdrawal checks and profitability calculation
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from utils.exchange_config import (
    get_exchange_config, 
    calculate_total_fees, 
    estimate_arbitrage_time
)

logger = logging.getLogger(__name__)

class ArbitrageAnalyzer:
    """Advanced arbitrage opportunity analyzer"""
    
    def __init__(self, exchange_service):
        self.exchange_service = exchange_service
        self.cache = {}  # Cache for network status
        self.cache_ttl = 300  # 5 minutes
    
    async def analyze_opportunity(
        self,
        user_id: str,
        coin: str,
        exchange_from: str,
        exchange_to: str,
        order_size_usdt: float = 100
    ) -> Dict:
        """
        Complete analysis of arbitrage opportunity
        Returns detailed breakdown with profitability score
        """
        try:
            # 1. Get current prices
            prices = await self._get_prices(user_id, coin, [exchange_from, exchange_to])
            if not prices:
                return self._create_error_result("Failed to fetch prices")
            
            buy_price = prices[exchange_from]['ask']
            sell_price = prices[exchange_to]['bid']
            
            # 2. Calculate raw spread
            raw_spread_percent = ((sell_price - buy_price) / buy_price) * 100
            
            # 3. Check deposit/withdrawal status
            network_status = await self._check_network_status(coin, [exchange_from, exchange_to])
            
            # 4. Calculate fees
            fees = self._calculate_all_fees(
                exchange_from, 
                exchange_to, 
                coin, 
                order_size_usdt, 
                buy_price
            )
            
            # 5. Calculate net profit
            net_profit = self._calculate_net_profit(
                order_size_usdt,
                buy_price,
                sell_price,
                fees
            )
            
            # 6. Estimate execution time
            execution_time = estimate_arbitrage_time(exchange_from, exchange_to)
            
            # 7. Calculate risk score
            risk_score = self._calculate_risk_score(
                raw_spread_percent,
                network_status,
                execution_time,
                prices
            )
            
            # 8. Calculate profitability score (0-100)
            profitability_score = self._calculate_profitability_score(
                net_profit['profit_percent'],
                risk_score,
                execution_time,
                network_status
            )
            
            # 9. Generate recommendation
            recommendation = self._generate_recommendation(
                profitability_score,
                net_profit,
                network_status
            )
            
            return {
                'success': True,
                'coin': coin,
                'exchanges': {
                    'from': exchange_from,
                    'to': exchange_to
                },
                'prices': {
                    'buy': buy_price,
                    'sell': sell_price,
                    'raw_spread_percent': round(raw_spread_percent, 3)
                },
                'fees': fees,
                'net_profit': net_profit,
                'network_status': network_status,
                'timing': {
                    'estimated_execution_seconds': execution_time,
                    'estimated_execution_minutes': round(execution_time / 60, 1)
                },
                'scores': {
                    'profitability': profitability_score,
                    'risk': risk_score
                },
                'recommendation': recommendation,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing arbitrage: {str(e)}")
            return self._create_error_result(str(e))
    
    async def find_best_opportunities(
        self,
        user_id: str,
        coins: List[str],
        exchanges: List[str],
        min_profit_percent: float = 0.5,
        order_size_usdt: float = 100
    ) -> List[Dict]:
        """
        Scan multiple coins and exchange pairs to find best opportunities
        """
        opportunities = []
        
        # Generate all exchange pairs
        pairs = []
        for i, ex1 in enumerate(exchanges):
            for ex2 in exchanges[i+1:]:
                pairs.append((ex1, ex2))
        
        # Analyze each coin on each pair
        for coin in coins:
            for ex_from, ex_to in pairs:
                # Analyze both directions
                for direction in [(ex_from, ex_to), (ex_to, ex_from)]:
                    try:
                        result = await self.analyze_opportunity(
                            user_id, coin, direction[0], direction[1], order_size_usdt
                        )
                        
                        if result['success'] and \
                           result['net_profit']['profit_percent'] >= min_profit_percent:
                            opportunities.append(result)
                            
                    except Exception as e:
                        logger.error(f"Error analyzing {coin} {direction}: {str(e)}")
                        continue
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.1)
        
        # Sort by profitability score
        opportunities.sort(key=lambda x: x['scores']['profitability'], reverse=True)
        
        return opportunities[:10]  # Return top 10
    
    async def _get_prices(self, user_id: str, coin: str, exchanges: List[str]) -> Dict:
        """Get bid/ask prices from exchanges"""
        prices = {}
        
        for exchange_id in exchanges:
            try:
                exchange = self.exchange_service._get_exchange(user_id, exchange_id)
                ticker = await exchange.fetch_ticker(f"{coin}/USDT")
                
                prices[exchange_id] = {
                    'bid': ticker['bid'],
                    'ask': ticker['ask'],
                    'last': ticker['last'],
                    'volume': ticker.get('quoteVolume', 0)
                }
            except Exception as e:
                logger.error(f"Error fetching price from {exchange_id}: {str(e)}")
                return {}
        
        return prices
    
    async def _check_network_status(self, coin: str, exchanges: List[str]) -> Dict:
        """
        Check if deposits and withdrawals are enabled
        Uses cache to reduce API calls
        """
        cache_key = f"network_{coin}_{'_'.join(sorted(exchanges))}"
        
        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if (datetime.now() - cached['timestamp']).seconds < self.cache_ttl:
                return cached['data']
        
        status = {}
        
        for exchange_id in exchanges:
            try:
                # Get network info from exchange
                # Note: Not all exchanges provide this via CCXT
                # This is a simplified version
                config = get_exchange_config(exchange_id)
                
                # In production, fetch real status from exchange API
                # For now, assume enabled if exchange is in config
                status[exchange_id] = {
                    'deposit_enabled': True,   # Should fetch from API
                    'withdrawal_enabled': True, # Should fetch from API
                    'network': 'TRC20',        # Default network
                    'min_withdrawal': config['withdrawal_fees'].get(coin, 0) * 10
                }
                
            except Exception as e:
                logger.error(f"Error checking network status for {exchange_id}: {str(e)}")
                status[exchange_id] = {
                    'deposit_enabled': False,
                    'withdrawal_enabled': False,
                    'network': 'unknown',
                    'min_withdrawal': 0
                }
        
        # Cache result
        self.cache[cache_key] = {
            'data': status,
            'timestamp': datetime.now()
        }
        
        return status
    
    def _calculate_all_fees(
        self,
        exchange_from: str,
        exchange_to: str,
        coin: str,
        order_size_usdt: float,
        buy_price: float
    ) -> Dict:
        """Calculate all fees involved in arbitrage"""
        config_from = get_exchange_config(exchange_from)
        config_to = get_exchange_config(exchange_to)
        
        amount_crypto = order_size_usdt / buy_price
        
        # Trading fees
        buy_fee_percent = config_from['fees']['taker']
        sell_fee_percent = config_to['fees']['taker']
        
        buy_fee = (order_size_usdt * buy_fee_percent) / 100
        sell_fee = (order_size_usdt * sell_fee_percent) / 100
        
        # Withdrawal fee
        withdrawal_fee_crypto = config_from['withdrawal_fees'].get(coin, 0)
        withdrawal_fee_usdt = withdrawal_fee_crypto * buy_price
        
        # Network fee (blockchain)
        network_fee_usdt = 0.5  # Estimate, depends on network congestion
        
        total_fees = buy_fee + sell_fee + withdrawal_fee_usdt + network_fee_usdt
        total_fees_percent = (total_fees / order_size_usdt) * 100
        
        return {
            'buy_fee': round(buy_fee, 2),
            'buy_fee_percent': buy_fee_percent,
            'sell_fee': round(sell_fee, 2),
            'sell_fee_percent': sell_fee_percent,
            'withdrawal_fee': round(withdrawal_fee_usdt, 2),
            'withdrawal_fee_crypto': withdrawal_fee_crypto,
            'network_fee': round(network_fee_usdt, 2),
            'total_fees': round(total_fees, 2),
            'total_fees_percent': round(total_fees_percent, 3)
        }
    
    def _calculate_net_profit(
        self,
        order_size: float,
        buy_price: float,
        sell_price: float,
        fees: Dict
    ) -> Dict:
        """Calculate net profit after all fees"""
        # Gross profit
        gross_profit = ((sell_price - buy_price) / buy_price) * order_size
        
        # Net profit
        net_profit = gross_profit - fees['total_fees']
        net_profit_percent = (net_profit / order_size) * 100
        
        # ROI
        roi = (net_profit / order_size) * 100
        
        return {
            'gross_profit': round(gross_profit, 2),
            'net_profit': round(net_profit, 2),
            'profit_percent': round(net_profit_percent, 3),
            'roi': round(roi, 2),
            'is_profitable': net_profit > 0
        }
    
    def _calculate_risk_score(
        self,
        spread: float,
        network_status: Dict,
        execution_time: int,
        prices: Dict
    ) -> int:
        """
        Calculate risk score (0-100, lower is better)
        """
        risk = 0
        
        # Spread too small = high risk
        if spread < 0.5:
            risk += 40
        elif spread < 1.0:
            risk += 20
        elif spread < 2.0:
            risk += 10
        
        # Network issues = high risk
        for exchange, status in network_status.items():
            if not status['deposit_enabled']:
                risk += 30
            if not status['withdrawal_enabled']:
                risk += 30
        
        # Long execution time = higher risk (price can change)
        if execution_time > 600:  # > 10 min
            risk += 25
        elif execution_time > 300:  # > 5 min
            risk += 15
        elif execution_time > 180:  # > 3 min
            risk += 10
        
        # Low volume = higher risk (slippage)
        for exchange, price_data in prices.items():
            if price_data.get('volume', 0) < 100000:  # < $100k volume
                risk += 15
        
        return min(risk, 100)  # Cap at 100
    
    def _calculate_profitability_score(
        self,
        profit_percent: float,
        risk_score: int,
        execution_time: int,
        network_status: Dict
    ) -> int:
        """
        Calculate profitability score (0-100, higher is better)
        """
        score = 0
        
        # Profit weight (60%)
        if profit_percent >= 5.0:
            score += 60
        elif profit_percent >= 3.0:
            score += 50
        elif profit_percent >= 2.0:
            score += 40
        elif profit_percent >= 1.0:
            score += 30
        elif profit_percent >= 0.5:
            score += 20
        else:
            score += max(0, int(profit_percent * 20))
        
        # Risk weight (25%) - inverse
        score += int((100 - risk_score) * 0.25)
        
        # Speed weight (10%)
        if execution_time < 120:
            score += 10
        elif execution_time < 300:
            score += 7
        elif execution_time < 600:
            score += 5
        else:
            score += 2
        
        # Network health weight (5%)
        all_enabled = all(
            status['deposit_enabled'] and status['withdrawal_enabled']
            for status in network_status.values()
        )
        if all_enabled:
            score += 5
        
        return min(score, 100)
    
    def _generate_recommendation(
        self,
        score: int,
        net_profit: Dict,
        network_status: Dict
    ) -> Dict:
        """Generate human-readable recommendation"""
        # Check network issues
        network_issues = []
        for exchange, status in network_status.items():
            if not status['deposit_enabled']:
                network_issues.append(f"{exchange}: deposits disabled")
            if not status['withdrawal_enabled']:
                network_issues.append(f"{exchange}: withdrawals disabled")
        
        # Generate rating
        if score >= 80:
            rating = "Excellent"
            action = "Highly Recommended"
            emoji = "🟢"
        elif score >= 60:
            rating = "Good"
            action = "Recommended"
            emoji = "🟡"
        elif score >= 40:
            rating = "Fair"
            action = "Proceed with Caution"
            emoji = "🟠"
        else:
            rating = "Poor"
            action = "Not Recommended"
            emoji = "🔴"
        
        # Generate message
        if net_profit['is_profitable']:
            profit_msg = f"Expected profit: ${net_profit['net_profit']} ({net_profit['profit_percent']}%)"
        else:
            profit_msg = f"Not profitable after fees (loss: ${abs(net_profit['net_profit'])})"
        
        warnings = []
        if network_issues:
            warnings.extend(network_issues)
        if score < 50:
            warnings.append("Low profitability score")
        
        return {
            'rating': rating,
            'action': action,
            'emoji': emoji,
            'message': profit_msg,
            'warnings': warnings if warnings else None
        }
    
    def _create_error_result(self, error: str) -> Dict:
        """Create error result"""
        return {
            'success': False,
            'error': error,
            'recommendation': {
                'rating': 'Error',
                'action': 'Cannot Analyze',
                'emoji': '❌',
                'message': error
            }
        }
