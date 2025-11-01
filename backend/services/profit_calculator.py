# backend/services/profit_calculator.py
"""
Precise profit calculator before starting arbitrage
Takes into account ALL fees, parameters, and market conditions
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from utils.exchange_config import get_exchange_config

logger = logging.getLogger(__name__)

class ProfitCalculator:
    """
    Calculate precise expected profit before starting arbitrage
    Considers: order size, fees, stop loss, take profit, frequency
    """
    
    def __init__(self, exchange_service):
        self.exchange_service = exchange_service
    
    async def calculate_expected_profit(
        self,
        user_id: str,
        coin: str,
        buy_exchange: str,
        sell_exchange: str,
        order_size: float,
        stop_loss_percent: float = 2.0,
        take_profit_percent: float = 5.0,
        frequency: str = 'medium',  # low, medium, high
        trading_hours: int = 24
    ) -> Dict:
        """
        Calculate expected profit with detailed breakdown
        
        Args:
            user_id: User ID
            coin: Cryptocurrency symbol
            buy_exchange: Exchange to buy from
            sell_exchange: Exchange to sell on
            order_size: Order size in USDT
            stop_loss_percent: Stop loss percentage
            take_profit_percent: Take profit percentage
            frequency: Trading frequency (affects number of trades)
            trading_hours: Hours of trading per day
        
        Returns:
            Detailed profit breakdown with scenarios
        """
        try:
            # 1. Get current prices
            prices = await self._get_current_prices(
                user_id, coin, [buy_exchange, sell_exchange]
            )
            
            if not prices:
                return self._create_error_result("Failed to fetch prices")
            
            buy_price = prices[buy_exchange]['ask']
            sell_price = prices[sell_exchange]['bid']
            
            # 2. Calculate single trade profit
            single_trade = await self._calculate_single_trade(
                coin, buy_exchange, sell_exchange,
                buy_price, sell_price, order_size
            )
            
            # 3. Estimate number of trades based on frequency
            trades_per_period = self._estimate_trades(frequency, trading_hours)
            
            # 4. Calculate scenarios (best, average, worst)
            scenarios = self._calculate_scenarios(
                single_trade,
                trades_per_period,
                stop_loss_percent,
                take_profit_percent
            )
            
            # 5. Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(
                single_trade,
                stop_loss_percent,
                take_profit_percent,
                order_size
            )
            
            # 6. Estimate execution success rate
            success_rate = await self._estimate_success_rate(
                coin, buy_exchange, sell_exchange, single_trade
            )
            
            # 7. Generate summary and recommendations
            summary = self._generate_summary(
                single_trade, scenarios, risk_metrics, success_rate
            )
            
            return {
                'success': True,
                'coin': coin,
                'exchanges': {
                    'buy': buy_exchange,
                    'sell': sell_exchange
                },
                'current_prices': {
                    'buy': buy_price,
                    'sell': sell_price
                },
                'order_size': order_size,
                'single_trade': single_trade,
                'trading_parameters': {
                    'frequency': frequency,
                    'stop_loss_percent': stop_loss_percent,
                    'take_profit_percent': take_profit_percent,
                    'trading_hours': trading_hours,
                    'estimated_trades_per_day': trades_per_period['per_day']
                },
                'scenarios': scenarios,
                'risk_metrics': risk_metrics,
                'success_rate': success_rate,
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating profit: {str(e)}")
            return self._create_error_result(str(e))
    
    async def _get_current_prices(
        self,
        user_id: str,
        coin: str,
        exchanges: List[str]
    ) -> Dict:
        """Get current bid/ask prices"""
        prices = {}
        
        for exchange_id in exchanges:
            try:
                if user_id in self.exchange_service.exchanges and \
                   exchange_id in self.exchange_service.exchanges[user_id]:
                    exchange = self.exchange_service._get_exchange(user_id, exchange_id)
                else:
                    # Use public API
                    exchange_class = self.exchange_service.supported_exchanges[exchange_id]
                    exchange = exchange_class({'enableRateLimit': True})
                
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
    
    async def _calculate_single_trade(
        self,
        coin: str,
        buy_exchange: str,
        sell_exchange: str,
        buy_price: float,
        sell_price: float,
        order_size: float
    ) -> Dict:
        """Calculate profit for single arbitrage cycle"""
        # Get configs
        buy_config = get_exchange_config(buy_exchange)
        sell_config = get_exchange_config(sell_exchange)
        
        # Calculate amount in crypto
        amount_crypto = order_size / buy_price
        
        # === FEES BREAKDOWN ===
        
        # 1. Trading fees
        buy_fee_percent = buy_config['fees']['taker']
        sell_fee_percent = sell_config['fees']['taker']
        buy_fee = (order_size * buy_fee_percent) / 100
        sell_fee = (order_size * sell_fee_percent) / 100
        
        # 2. Withdrawal fee
        withdrawal_fee_crypto = buy_config['withdrawal_fees'].get(coin, 0)
        withdrawal_fee_usdt = withdrawal_fee_crypto * buy_price
        
        # 3. Network fee (blockchain gas)
        network_fee = 0.5  # Conservative estimate
        
        # 4. Slippage (price movement during execution)
        slippage_percent = 0.1  # 0.1% average slippage
        slippage_cost = (order_size * slippage_percent) / 100
        
        # Total fees
        total_fees = buy_fee + sell_fee + withdrawal_fee_usdt + network_fee + slippage_cost
        total_fees_percent = (total_fees / order_size) * 100
        
        # === PROFIT CALCULATION ===
        
        # Gross profit (before fees)
        gross_profit = ((sell_price - buy_price) / buy_price) * order_size
        gross_profit_percent = ((sell_price - buy_price) / buy_price) * 100
        
        # Net profit (after all fees)
        net_profit = gross_profit - total_fees
        net_profit_percent = (net_profit / order_size) * 100
        
        # Amount received after selling
        amount_after_fees = amount_crypto - withdrawal_fee_crypto
        proceeds_from_sale = amount_after_fees * sell_price
        
        # === TIMING ===
        execution_time = (
            5 +  # Buy order execution
            buy_config['withdrawal_time'] +
            sell_config['deposit_time'] +
            5  # Sell order execution
        )
        
        return {
            'order_size': order_size,
            'buy_price': round(buy_price, 8),
            'sell_price': round(sell_price, 8),
            'amount_crypto': round(amount_crypto, 8),
            'spread': {
                'absolute': round(sell_price - buy_price, 8),
                'percent': round(gross_profit_percent, 3)
            },
            'fees': {
                'buy_trading_fee': round(buy_fee, 2),
                'sell_trading_fee': round(sell_fee, 2),
                'withdrawal_fee': round(withdrawal_fee_usdt, 2),
                'network_fee': round(network_fee, 2),
                'slippage': round(slippage_cost, 2),
                'total_fees': round(total_fees, 2),
                'total_fees_percent': round(total_fees_percent, 3)
            },
            'profit': {
                'gross_profit': round(gross_profit, 2),
                'gross_profit_percent': round(gross_profit_percent, 3),
                'net_profit': round(net_profit, 2),
                'net_profit_percent': round(net_profit_percent, 3),
                'roi': round(net_profit_percent, 2)
            },
            'timing': {
                'execution_seconds': execution_time,
                'execution_minutes': round(execution_time / 60, 1)
            },
            'is_profitable': net_profit > 0
        }
    
    def _estimate_trades(self, frequency: str, trading_hours: int) -> Dict:
        """Estimate number of trades based on frequency"""
        # Trades per hour based on frequency
        trades_per_hour = {
            'low': 0.5,      # 1 trade per 2 hours
            'medium': 1.5,   # ~1.5 trades per hour
            'high': 3        # 3 trades per hour
        }
        
        rate = trades_per_hour.get(frequency, 1.5)
        
        per_day = rate * trading_hours
        per_week = per_day * 7
        per_month = per_day * 30
        
        return {
            'per_hour': rate,
            'per_day': round(per_day, 1),
            'per_week': round(per_week, 1),
            'per_month': round(per_month, 1)
        }
    
    def _calculate_scenarios(
        self,
        single_trade: Dict,
        trades: Dict,
        stop_loss: float,
        take_profit: float
    ) -> Dict:
        """Calculate best, average, and worst case scenarios"""
        net_profit = single_trade['profit']['net_profit']
        order_size = single_trade['order_size']
        
        # Win rate estimates (based on market conditions)
        win_rate_best = 0.85     # 85% successful trades
        win_rate_average = 0.70  # 70% successful trades
        win_rate_worst = 0.50    # 50% successful trades
        
        def calculate_scenario(win_rate: float, trades_per_day: float):
            """Calculate scenario with given win rate"""
            winning_trades = trades_per_day * win_rate
            losing_trades = trades_per_day * (1 - win_rate)
            
            # Profit from winning trades
            profit_from_wins = winning_trades * net_profit
            
            # Loss from losing trades (stop loss activated)
            loss_per_trade = (order_size * stop_loss) / 100
            loss_from_losses = losing_trades * loss_per_trade
            
            # Net daily profit
            net_daily = profit_from_wins - loss_from_losses
            
            return {
                'trades_per_day': round(trades_per_day, 1),
                'winning_trades': round(winning_trades, 1),
                'losing_trades': round(losing_trades, 1),
                'win_rate': round(win_rate * 100, 1),
                'profit_from_wins': round(profit_from_wins, 2),
                'loss_from_losses': round(loss_from_losses, 2),
                'net_daily_profit': round(net_daily, 2),
                'net_weekly_profit': round(net_daily * 7, 2),
                'net_monthly_profit': round(net_daily * 30, 2)
            }
        
        return {
            'best_case': calculate_scenario(win_rate_best, trades['per_day']),
            'average_case': calculate_scenario(win_rate_average, trades['per_day']),
            'worst_case': calculate_scenario(win_rate_worst, trades['per_day'])
        }
    
    def _calculate_risk_metrics(
        self,
        single_trade: Dict,
        stop_loss: float,
        take_profit: float,
        order_size: float
    ) -> Dict:
        """Calculate risk metrics"""
        net_profit = single_trade['profit']['net_profit']
        
        # Maximum loss per trade (if stop loss hit)
        max_loss = (order_size * stop_loss) / 100
        
        # Maximum gain per trade (if take profit hit)
        max_gain = (order_size * take_profit) / 100
        
        # Risk-reward ratio
        risk_reward = max_gain / max_loss if max_loss > 0 else 0
        
        # Break-even win rate (what % needs to win to break even)
        break_even_rate = (max_loss / (max_gain + max_loss)) * 100 if (max_gain + max_loss) > 0 else 0
        
        return {
            'max_loss_per_trade': round(max_loss, 2),
            'max_gain_per_trade': round(max_gain, 2),
            'risk_reward_ratio': round(risk_reward, 2),
            'break_even_win_rate': round(break_even_rate, 1),
            'recommended_win_rate': 70.0  # Need 70%+ to be profitable
        }
    
    async def _estimate_success_rate(
        self,
        coin: str,
        buy_exchange: str,
        sell_exchange: str,
        single_trade: Dict
    ) -> Dict:
        """Estimate success rate based on various factors"""
        # Base success rate
        success_rate = 85.0
        
        # Adjust based on spread size
        spread = single_trade['spread']['percent']
        if spread < 0.5:
            success_rate -= 20  # Very tight spread = higher failure risk
        elif spread < 1.0:
            success_rate -= 10
        elif spread > 2.0:
            success_rate += 5  # Good spread = higher success
        
        # Adjust based on execution time
        exec_time = single_trade['timing']['execution_minutes']
        if exec_time > 10:
            success_rate -= 15  # Long time = price can move
        elif exec_time > 5:
            success_rate -= 8
        
        # Adjust based on profitability
        net_profit_percent = single_trade['profit']['net_profit_percent']
        if net_profit_percent < 0.3:
            success_rate -= 15  # Low profit = barely worth it
        elif net_profit_percent > 2.0:
            success_rate += 10  # High profit = good opportunity
        
        success_rate = max(40, min(95, success_rate))  # Clamp between 40-95%
        
        return {
            'estimated_rate': round(success_rate, 1),
            'confidence': 'High' if spread > 1.5 else 'Medium' if spread > 0.8 else 'Low'
        }
    
    def _generate_summary(
        self,
        single_trade: Dict,
        scenarios: Dict,
        risk_metrics: Dict,
        success_rate: Dict
    ) -> Dict:
        """Generate human-readable summary"""
        avg_case = scenarios['average_case']
        net_profit = single_trade['profit']['net_profit']
        
        # Overall rating
        if net_profit <= 0:
            rating = "Not Profitable"
            emoji = "🔴"
            recommendation = "Don't Start"
        elif avg_case['net_monthly_profit'] < 100:
            rating = "Low Profit"
            emoji = "🟠"
            recommendation = "Increase order size or frequency"
        elif avg_case['net_monthly_profit'] < 500:
            rating = "Moderate"
            emoji = "🟡"
            recommendation = "Acceptable for testing"
        elif avg_case['net_monthly_profit'] < 2000:
            rating = "Good"
            emoji = "🟢"
            recommendation = "Profitable setup"
        else:
            rating = "Excellent"
            emoji = "🟢🟢"
            recommendation = "Highly profitable!"
        
        return {
            'rating': rating,
            'emoji': emoji,
            'recommendation': recommendation,
            'key_points': [
                f"Single trade profit: ${net_profit:.2f}",
                f"Expected monthly (average): ${avg_case['net_monthly_profit']:.2f}",
                f"Win rate needed: {risk_metrics['recommended_win_rate']}%",
                f"Estimated success: {success_rate['estimated_rate']}%"
            ],
            'is_recommended': net_profit > 0 and avg_case['net_monthly_profit'] > 100
        }
    
    def _create_error_result(self, error: str) -> Dict:
        """Create error result"""
        return {
            'success': False,
            'error': error
        }

# Global instance
calculator = ProfitCalculator(None)  # Will be initialized with exchange_service
