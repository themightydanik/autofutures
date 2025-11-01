# backend/services/coingecko_service.py
"""
CoinGecko API integration for additional market data
FREE API - No key required!
"""
import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CoinGeckoService:
    """
    Free market data from CoinGecko
    Rate limit: 50 calls/minute
    """
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 60  # 1 minute
        self.last_request = datetime.now()
        self.request_delay = 1.2  # seconds between requests
    
    async def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        elapsed = (datetime.now() - self.last_request).total_seconds()
        if elapsed < self.request_delay:
            await asyncio.sleep(self.request_delay - elapsed)
        self.last_request = datetime.now()
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with rate limiting"""
        await self._rate_limit()
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"CoinGecko API error: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Error calling CoinGecko: {str(e)}")
            return {}
    
    async def get_coin_info(self, coin_id: str) -> Dict:
        """
        Get detailed coin information
        Example: coin_id = 'bitcoin', 'ethereum', 'solana'
        """
        cache_key = f"coin_info_{coin_id}"
        
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if (datetime.now() - cached['timestamp']).seconds < self.cache_ttl:
                return cached['data']
        
        data = await self._make_request(f"/coins/{coin_id}")
        
        if data:
            result = {
                'id': data.get('id'),
                'symbol': data.get('symbol', '').upper(),
                'name': data.get('name'),
                'current_price': data.get('market_data', {}).get('current_price', {}).get('usd'),
                'market_cap': data.get('market_data', {}).get('market_cap', {}).get('usd'),
                'total_volume': data.get('market_data', {}).get('total_volume', {}).get('usd'),
                'price_change_24h': data.get('market_data', {}).get('price_change_percentage_24h'),
                'ath': data.get('market_data', {}).get('ath', {}).get('usd'),
                'atl': data.get('market_data', {}).get('atl', {}).get('usd'),
                'circulating_supply': data.get('market_data', {}).get('circulating_supply'),
                'total_supply': data.get('market_data', {}).get('total_supply'),
            }
            
            self.cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }
            
            return result
        
        return {}
    
    async def get_trending_coins(self) -> List[Dict]:
        """Get trending coins (searches, most visited)"""
        data = await self._make_request("/search/trending")
        
        if data and 'coins' in data:
            trending = []
            for item in data['coins'][:10]:
                coin = item['item']
                trending.append({
                    'id': coin.get('id'),
                    'symbol': coin.get('symbol', '').upper(),
                    'name': coin.get('name'),
                    'market_cap_rank': coin.get('market_cap_rank'),
                    'thumb': coin.get('thumb'),
                    'score': coin.get('score', 0)
                })
            return trending
        
        return []
    
    async def get_exchange_rates(self) -> Dict:
        """Get current exchange rates for various currencies"""
        data = await self._make_request("/exchange_rates")
        
        if data and 'rates' in data:
            return data['rates']
        
        return {}
    
    async def get_market_overview(self) -> Dict:
        """Get global market overview"""
        data = await self._make_request("/global")
        
        if data and 'data' in data:
            global_data = data['data']
            return {
                'total_market_cap_usd': global_data.get('total_market_cap', {}).get('usd'),
                'total_volume_24h_usd': global_data.get('total_volume', {}).get('usd'),
                'market_cap_change_24h': global_data.get('market_cap_change_percentage_24h_usd'),
                'bitcoin_dominance': global_data.get('market_cap_percentage', {}).get('btc'),
                'ethereum_dominance': global_data.get('market_cap_percentage', {}).get('eth'),
                'active_cryptocurrencies': global_data.get('active_cryptocurrencies'),
                'markets': global_data.get('markets'),
                'updated_at': global_data.get('updated_at')
            }
        
        return {}
    
    async def compare_exchange_prices(self, coin_id: str, exchanges: List[str]) -> Dict:
        """
        Compare prices across exchanges
        Useful for finding arbitrage opportunities
        """
        data = await self._make_request(f"/coins/{coin_id}/tickers")
        
        if not data or 'tickers' not in data:
            return {}
        
        exchange_prices = {}
        
        for ticker in data['tickers']:
            exchange = ticker.get('market', {}).get('identifier', '').lower()
            
            if exchange in exchanges or not exchanges:
                if ticker.get('target') == 'USDT':
                    if exchange not in exchange_prices:
                        exchange_prices[exchange] = []
                    
                    exchange_prices[exchange].append({
                        'price': ticker.get('last'),
                        'volume': ticker.get('volume'),
                        'bid': ticker.get('bid_ask_spread_percentage'),
                        'trust_score': ticker.get('trust_score'),
                        'timestamp': ticker.get('timestamp')
                    })
        
        # Get average price per exchange
        result = {}
        for exchange, prices in exchange_prices.items():
            if prices:
                avg_price = sum(p['price'] for p in prices) / len(prices)
                total_volume = sum(p['volume'] for p in prices)
                
                result[exchange] = {
                    'average_price': avg_price,
                    'total_volume': total_volume,
                    'price_count': len(prices)
                }
        
        return result
    
    async def get_coin_market_chart(
        self, 
        coin_id: str, 
        vs_currency: str = 'usd',
        days: int = 1
    ) -> Dict:
        """Get historical market data (price, volume, market cap)"""
        params = {
            'vs_currency': vs_currency,
            'days': days
        }
        
        data = await self._make_request(f"/coins/{coin_id}/market_chart", params)
        
        if data:
            return {
                'prices': data.get('prices', []),
                'volumes': data.get('total_volumes', []),
                'market_caps': data.get('market_caps', [])
            }
        
        return {}
    
    def map_symbol_to_id(self, symbol: str) -> str:
        """
        Map common symbols to CoinGecko IDs
        """
        mapping = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'SOL': 'solana',
            'BNB': 'binancecoin',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'DOGE': 'dogecoin',
            'MATIC': 'matic-network',
            'DOT': 'polkadot',
            'AVAX': 'avalanche-2',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'USDT': 'tether',
            'USDC': 'usd-coin'
        }
        
        return mapping.get(symbol.upper(), symbol.lower())

# Global instance
coingecko = CoinGeckoService()
