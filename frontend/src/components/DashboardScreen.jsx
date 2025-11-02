// frontend/src/components/DashboardScreen.jsx
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { 
  TrendingUp, Settings, LogOut, Play, Square, Activity, 
  CheckCircle, Clock, ArrowRight, DollarSign, BarChart3, Zap, 
  Search 
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTrading } from '../context/TradingContext';
import api from '../services/api';

const DashboardScreen = ({ onOpenSettings }) => {
  const { user, logout } = useAuth();
  const {
    isTrading,
    settings,
    tradeParams,
    activeTrades,
    botLogs,
    balances,
    pnl,
    setTradeParams,
    startTrading,
    stopTrading,
  } = useTrading();

  const [priceData, setPriceData] = useState([]);
  const [selectedCoin, setSelectedCoin] = useState(tradeParams.coin || 'BTC');
  const [showCoinSelector, setShowCoinSelector] = useState(false);
  const [pnlInUSDT, setPnlInUSDT] = useState(false);
  const [coins, setCoins] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [localParams, setLocalParams] = useState(tradeParams);

  // Load initial data
  useEffect(() => {
    loadCoins();
    loadStatistics();
    loadPriceHistory(selectedCoin);
  }, []);

  // Update price history when coin changes
  useEffect(() => {
    loadPriceHistory(selectedCoin);
  }, [selectedCoin]);

  const loadCoins = async () => {
    try {
      const topCoins = await api.getTopCoins(10);
      setCoins(topCoins);
    } catch (error) {
      console.error('Failed to load coins:', error);
      // Fallback to default coins
      setCoins([
        { symbol: 'BTC', name: 'Bitcoin', price: 42280, change: 2.4 },
        { symbol: 'ETH', name: 'Ethereum', price: 2257, change: 1.8 },
        { symbol: 'SOL', name: 'Solana', price: 142.50, change: -0.5 },
      ]);
    }
  };

  const loadStatistics = async () => {
    try {
      const stats = await api.getStatistics();
      setStatistics(stats);
    } catch (error) {
      console.error('Failed to load statistics:', error);
    }
  };

  const loadPriceHistory = async (symbol) => {
    try {
      const history = await api.getPriceHistory(symbol, '1m', 50);
      setPriceData(history);
    } catch (error) {
      console.error('Failed to load price history:', error);
    }
  };

  const handleToggleTrading = async () => {
    if (isTrading) {
      await stopTrading();
    } else {
      await startTrading(localParams);
    }
  };

  const handleParamChange = (field, value) => {
    setLocalParams({
      ...localParams,
      [field]: value
    });
  };

  const handleSelectCoin = (coin) => {
    setSelectedCoin(coin);
    setShowCoinSelector(false);
    handleParamChange('coin', coin);
  };

  const getLogIcon = (type) => {
    switch(type) {
      case 'search': return <Search className="w-4 h-4 text-blue-400" />;
      case 'buy': case 'success': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'sell': return <Activity className="w-4 h-4 text-orange-400" />;
      case 'transfer': return <ArrowRight className="w-4 h-4 text-purple-400" />;
      case 'profit': return <DollarSign className="w-4 h-4 text-yellow-400" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const selectedCoinData = coins.find(c => c.symbol === selectedCoin) || {};
  const totalBalance = Object.values(balances).reduce((sum, balance) => sum + (balance || 0), 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Header */}
      <div className="bg-gray-800/50 backdrop-blur-xl border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <TrendingUp className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">AutoFutures</h1>
              <p className="text-xs text-gray-400">@{user?.username}</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={onOpenSettings}
              className="p-2 hover:bg-gray-700 rounded-lg transition"
            >
              <Settings className="w-5 h-5 text-gray-300" />
            </button>
            <button
              onClick={logout}
              className="p-2 hover:bg-gray-700 rounded-lg transition"
            >
              <LogOut className="w-5 h-5 text-gray-300" />
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Top Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-800/50 backdrop-blur-xl p-4 rounded-xl border border-gray-700">
            <div className="text-gray-400 text-xs mb-1">Вид торговли</div>
            <div className="text-white font-semibold">{settings?.trade_type === 'arbitrage' ? 'Арбитраж' : 'Маржинальная торговля'}</div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-xl p-4 rounded-xl border border-gray-700">
            <div className="flex items-center justify-between mb-1">
              <div className="text-gray-400 text-xs">PnL</div>
              <button
                onClick={() => setPnlInUSDT(!pnlInUSDT)}
                className="text-xs text-blue-400 hover:text-blue-300"
              >
                {pnlInUSDT ? 'USDT' : '%'}
              </button>
            </div>
            <div className={`text-xl font-bold ${pnl.total >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {pnl.total >= 0 ? '+' : ''}{pnlInUSDT ? `$${pnl.total.toFixed(2)}` : `${pnl.percent.toFixed(2)}%`}
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-xl p-4 rounded-xl border border-gray-700">
            <div className="text-gray-400 text-xs mb-1">Статус</div>
            <div className="flex items-center">
              <div className={`w-2 h-2 rounded-full mr-2 ${isTrading ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`}></div>
              <div className="text-white font-semibold text-sm">{isTrading ? 'Активен' : 'Остановлен'}</div>
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-xl p-4 rounded-xl border border-gray-700">
            <div className="text-gray-400 text-xs mb-1">Сделок сегодня</div>
            <div className="text-white font-bold text-xl">{statistics.trades_today || 0}</div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Left Column - Chart and Coin Selector */}
          <div className="lg:col-span-2 space-y-6">
            {/* Coin Selector */}
            <div className="bg-gray-800/50 backdrop-blur-xl p-4 rounded-xl border border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Выбранная монета</h3>
                <button
                  onClick={() => setShowCoinSelector(!showCoinSelector)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm"
                >
                  Изменить
                </button>
              </div>

              {showCoinSelector ? (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {coins.map(coin => (
                    <button
                      key={coin.symbol}
                      onClick={() => handleSelectCoin(coin.symbol)}
                      className={`p-3 rounded-lg border-2 transition ${
                        selectedCoin === coin.symbol
                          ? 'border-blue-500 bg-blue-500/20'
                          : 'border-gray-600 bg-gray-700/30 hover:border-gray-500'
                      }`}
                    >
                      <div className="text-white font-bold">{coin.symbol}</div>
                      <div className="text-gray-400 text-xs">{coin.name}</div>
                      <div className={`text-xs font-semibold mt-1 ${coin.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {coin.change >= 0 ? '+' : ''}{coin.change}%
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="flex items-center space-x-4">
                  <div className="flex-1">
                    <div className="text-2xl font-bold text-white">{selectedCoin}/USDT</div>
                    <div className="text-gray-400 text-sm">{selectedCoinData.name}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold text-white">${selectedCoinData.price?.toLocaleString()}</div>
                    <div className={`text-sm font-semibold ${selectedCoinData.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {selectedCoinData.change >= 0 ? '+' : ''}{selectedCoinData.change}%
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Price Chart */}
            <div className="bg-gray-800/50 backdrop-blur-xl p-6 rounded-xl border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">График цены {selectedCoin}/USDT</h3>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={priceData}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="time" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Area type="monotone" dataKey="price" stroke="#3B82F6" fillOpacity={1} fill="url(#colorPrice)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Active Trades */}
            <div className="bg-gray-800/50 backdrop-blur-xl p-6 rounded-xl border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Активные сделки</h3>
              <div className="space-y-3">
                {activeTrades && activeTrades.length > 0 ? activeTrades.map(trade => (
                  <div key={trade.id} className="bg-gray-700/30 p-4 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <BarChart3 className="w-4 h-4 text-blue-400" />
                        <span className="text-white font-semibold">{trade.coin}/USDT</span>
                        <span className="text-xs text-gray-400">{trade.trade_type}</span>
                      </div>
                      <div className={`text-sm font-bold ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {trade.pnl >= 0 ? '+' : ''}${trade.pnl?.toFixed(2)}
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <div className="text-gray-400 text-xs">Вход</div>
                        <div className="text-white">${trade.entry_price}</div>
                      </div>
                      <div>
                        <div className="text-gray-400 text-xs">Текущая</div>
                        <div className="text-white">${trade.current_price}</div>
                      </div>
                      <div>
                        <div className="text-gray-400 text-xs">PnL</div>
                        <div className={`font-semibold ${trade.pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {trade.pnl_percent >= 0 ? '+' : ''}{trade.pnl_percent}%
                        </div>
                      </div>
                    </div>
                  </div>
                )) : (
                  <div className="text-center text-gray-400 py-8">
                    Нет активных сделок
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Controls and Balances */}
          <div className="space-y-6">
            {/* Trading Controls */}
            <div className="bg-gray-800/50 backdrop-blur-xl p-6 rounded-xl border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Управление</h3>
              
              <button
                onClick={handleToggleTrading}
                className={`w-full py-4 rounded-xl font-semibold transition transform hover:scale-105 flex items-center justify-center space-x-2 mb-4 ${
                  isTrading
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
              >
                {isTrading ? (
                  <>
                    <Square className="w-5 h-5" />
                    <span>Остановить</span>
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    <span>Запустить</span>
                  </>
                )}
              </button>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Направление</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => handleParamChange('side', 'LONG')}
                      className={`py-2 rounded-lg transition text-sm font-semibold ${
                        localParams.side === 'LONG'
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      LONG
                    </button>
                    <button
                      onClick={() => handleParamChange('side', 'SHORT')}
                      className={`py-2 rounded-lg transition text-sm font-semibold ${
                        localParams.side === 'SHORT'
                          ? 'bg-red-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      SHORT
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Размер ордера ($)</label>
                  <input
                    type="number"
                    value={localParams.order_size}
                    onChange={(e) => handleParamChange('order_size', parseFloat(e.target.value))}
                    className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Stop Loss (%)</label>
                  <input
                    type="number"
                    value={localParams.stop_loss}
                    onChange={(e) => handleParamChange('stop_loss', parseFloat(e.target.value))}
                    className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Take Profit (%)</label>
                  <input
                    type="number"
                    value={localParams.take_profit}
                    onChange={(e) => handleParamChange('take_profit', parseFloat(e.target.value))}
                    className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Частота сделок</label>
                  <select
                    value={localParams.frequency}
                    onChange={(e) => handleParamChange('frequency', e.target.value)}
                    className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500 text-sm"
                  >
                    <option value="low">Низкая</option>
                    <option value="medium">Средняя</option>
                    <option value="high">Высокая</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Balances */}
            <div className="bg-gray-800/50 backdrop-blur-xl p-6 rounded-xl border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Балансы</h3>
              <div className="space-y-3">
                {settings?.exchanges?.map(exchangeId => (
                  <div key={exchangeId} className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg">
                    <span className="text-white text-sm font-medium capitalize">{exchangeId}</span>
                    <span className="text-green-400 font-semibold text-sm">
                      ${(balances[exchangeId] || 0).toFixed(2)}
                    </span>
                  </div>
                ))}
                <div className="pt-3 border-t border-gray-600">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-300 text-sm font-medium">Всего</span>
                    <span className="text-white font-bold">
                      ${totalBalance.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bot Activity Log */}
        <div className="bg-gray-800/50 backdrop-blur-xl p-6 rounded-xl border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Zap className="w-5 h-5 text-yellow-400" />
              <h3 className="text-lg font-semibold text-white">Активность бота</h3>
            </div>
            {isTrading && (
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-green-400 text-sm font-medium">В реальном времени</span>
              </div>
            )}
          </div>
          
          <div className="space-y-2 max-h-96 overflow-y-auto pr-2 custom-scrollbar">
            {botLogs && botLogs.length > 0 ? botLogs.map((log) => (
              <div
                key={log.id}
                className={`p-4 rounded-lg border transition-all ${
                  log.status === 'active'
                    ? 'bg-blue-500/10 border-blue-500/30'
                    : 'bg-gray-700/30 border-gray-600/30'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className="mt-0.5">{getLogIcon(log.log_type || log.type)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-400 font-mono">{log.time || new Date(log.timestamp).toLocaleTimeString()}</span>
                      {log.status === 'active' && (
                        <div className="flex items-center space-x-1">
                          <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse"></div>
                          <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                          <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                        </div>
                      )}
                    </div>
                    <p className="text-white text-sm">{log.message}</p>
                  </div>
                </div>
              </div>
            )) : (
              <div className="text-center text-gray-400 py-8">
                Нет логов активности
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(55, 65, 81, 0.3);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(59, 130, 246, 0.5);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(59, 130, 246, 0.7);
        }
      `}</style>
    </div>
  );
};

export default DashboardScreen;
