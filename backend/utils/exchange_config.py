# backend/utils/exchange_config.py
"""
Extended exchange configuration with support for top crypto exchanges
"""

SUPPORTED_EXCHANGES = {
    # Tier 1 - Highest liquidity
    'binance': {
        'name': 'Binance',
        'ccxt_id': 'binance',
        'enabled': True,
        'tier': 1,
        'countries': ['Global'],
        'has': {
            'spot': True,
            'futures': True,
            'margin': True,
            'swap': True
        },
        'fees': {
            'maker': 0.1,   # 0.1%
            'taker': 0.1
        },
        'withdrawal_fees': {
            'BTC': 0.0005,
            'ETH': 0.005,
            'USDT': 1.0,
            'BNB': 0.01
        },
        'deposit_time': 60,      # seconds (avg)
        'withdrawal_time': 300,  # seconds (avg)
        'limits': {
            'min_order': 10,     # USDT
            'max_order': 1000000
        }
    },
    
    'bybit': {
        'name': 'Bybit',
        'ccxt_id': 'bybit',
        'enabled': True,
        'tier': 1,
        'countries': ['Global'],
        'has': {
            'spot': True,
            'futures': True,
            'margin': True,
            'swap': True
        },
        'fees': {
            'maker': 0.1,
            'taker': 0.1
        },
        'withdrawal_fees': {
            'BTC': 0.0005,
            'ETH': 0.005,
            'USDT': 1.0
        },
        'deposit_time': 60,
        'withdrawal_time': 300,
        'limits': {
            'min_order': 10,
            'max_order': 500000
        }
    },
    
    'okx': {
        'name': 'OKX',
        'ccxt_id': 'okx',
        'enabled': True,
        'tier': 1,
        'countries': ['Global'],
        'has': {
            'spot': True,
            'futures': True,
            'margin': True,
            'swap': True
        },
        'fees': {
            'maker': 0.08,
            'taker': 0.1
        },
        'withdrawal_fees': {
            'BTC': 0.0004,
            'ETH': 0.003,
            'USDT': 0.8
        },
        'deposit_time': 50,
        'withdrawal_time': 250,
        'limits': {
            'min_order': 10,
            'max_order': 800000
        }
    },
    
    'gateio': {
        'name': 'Gate.io',
        'ccxt_id': 'gateio',
        'enabled': True,
        'tier': 2,
        'countries': ['Global'],
        'has': {
            'spot': True,
            'futures': True,
            'margin': True,
            'swap': True
        },
        'fees': {
            'maker': 0.2,
            'taker': 0.2
        },
        'withdrawal_fees': {
            'BTC': 0.001,
            'ETH': 0.01,
            'USDT': 2.0
        },
        'deposit_time': 70,
        'withdrawal_time': 350,
        'limits': {
            'min_order': 10,
            'max_order': 300000
        }
    },
    
    'kucoin': {
        'name': 'KuCoin',
        'ccxt_id': 'kucoin',
        'enabled': True,
        'tier': 2,
        'countries': ['Seychelles'],
        'has': {
            'spot': True,
            'futures': True,
            'margin': True,
            'swap': True
        },
        'fees': {
            'maker': 0.1,
            'taker': 0.1
        },
        'withdrawal_fees': {
            'BTC': 0.0005,
            'ETH': 0.005,
            'USDT': 1.0
        },
        'deposit_time': 60,
        'withdrawal_time': 300,
        'limits': {
            'min_order': 10,
            'max_order': 400000
        }
    },
    
    'kraken': {
        'name': 'Kraken',
        'ccxt_id': 'kraken',
        'enabled': True,
        'tier': 1,
        'countries': ['US', 'EU'],
        'has': {
            'spot': True,
            'futures': True,
            'margin': True,
            'swap': False
        },
        'fees': {
            'maker': 0.16,
            'taker': 0.26
        },
        'withdrawal_fees': {
            'BTC': 0.00015,
            'ETH': 0.0035,
            'USDT': 5.0
        },
        'deposit_time': 90,
        'withdrawal_time': 400,
        'limits': {
            'min_order': 10,
            'max_order': 500000
        }
    },
    
    'huobi': {
        'name': 'Huobi',
        'ccxt_id': 'huobi',
        'enabled': True,
        'tier': 2,
        'countries': ['Seychelles'],
        'has': {
            'spot': True,
            'futures': True,
            'margin': True,
            'swap': True
        },
        'fees': {
            'maker': 0.2,
            'taker': 0.2
        },
        'withdrawal_fees': {
            'BTC': 0.0005,
            'ETH': 0.004,
            'USDT': 2.0
        },
        'deposit_time': 65,
        'withdrawal_time': 320,
        'limits': {
            'min_order': 10,
            'max_order': 350000
        }
    },
    
    'bitfinex': {
        'name': 'Bitfinex',
        'ccxt_id': 'bitfinex',
        'enabled': True,
        'tier': 2,
        'countries': ['British Virgin Islands'],
        'has': {
            'spot': True,
            'futures': False,
            'margin': True,
            'swap': False
        },
        'fees': {
            'maker': 0.1,
            'taker': 0.2
        },
        'withdrawal_fees': {
            'BTC': 0.0004,
            'ETH': 0.0027,
            'USDT': 3.0
        },
        'deposit_time': 80,
        'withdrawal_time': 380,
        'limits': {
            'min_order': 10,
            'max_order': 600000
        }
    },
    
    'coinbase': {
        'name': 'Coinbase Pro',
        'ccxt_id': 'coinbasepro',
        'enabled': True,
        'tier': 1,
        'countries': ['US'],
        'has': {
            'spot': True,
            'futures': False,
            'margin': False,
            'swap': False
        },
        'fees': {
            'maker': 0.4,
            'taker': 0.6
        },
        'withdrawal_fees': {
            'BTC': 0,
            'ETH': 0,
            'USDT': 0
        },
        'deposit_time': 100,
        'withdrawal_time': 500,
        'limits': {
            'min_order': 10,
            'max_order': 1000000
        }
    },
    
    'bitget': {
        'name': 'Bitget',
        'ccxt_id': 'bitget',
        'enabled': True,
        'tier': 2,
        'countries': ['Singapore'],
        'has': {
            'spot': True,
            'futures': True,
            'margin': True,
            'swap': True
        },
        'fees': {
            'maker': 0.1,
            'taker': 0.1
        },
        'withdrawal_fees': {
            'BTC': 0.0005,
            'ETH': 0.005,
            'USDT': 1.0
        },
        'deposit_time': 60,
        'withdrawal_time': 300,
        'limits': {
            'min_order': 10,
            'max_order': 300000
        }
    }
}

def get_supported_exchanges(tier: int = None, enabled_only: bool = True):
    """Get list of supported exchanges"""
    exchanges = SUPPORTED_EXCHANGES.copy()
    
    if enabled_only:
        exchanges = {k: v for k, v in exchanges.items() if v['enabled']}
    
    if tier:
        exchanges = {k: v for k, v in exchanges.items() if v['tier'] == tier}
    
    return exchanges

def get_exchange_config(exchange_id: str):
    """Get configuration for specific exchange"""
    return SUPPORTED_EXCHANGES.get(exchange_id)

def calculate_total_fees(exchange_id: str, amount: float, coin: str = 'BTC'):
    """Calculate total fees for arbitrage"""
    config = get_exchange_config(exchange_id)
    if not config:
        return 0
    
    # Trading fees (buy + sell)
    trading_fees = (config['fees']['taker'] * 2) * amount / 100
    
    # Withdrawal fee
    withdrawal_fee = config['withdrawal_fees'].get(coin, 0)
    
    return trading_fees + withdrawal_fee

def estimate_arbitrage_time(from_exchange: str, to_exchange: str):
    """Estimate time for complete arbitrage cycle"""
    from_config = get_exchange_config(from_exchange)
    to_config = get_exchange_config(to_exchange)
    
    if not from_config or not to_config:
        return 0
    
    # Buy on first exchange + withdraw + deposit to second + sell
    total_time = (
        5 +  # Buy order execution
        from_config['withdrawal_time'] +
        to_config['deposit_time'] +
        5  # Sell order execution
    )
    
    return total_time  # seconds
