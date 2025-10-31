import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { TrendingUp, TrendingDown, Settings, LogOut, Play, Square, Search, Activity, CheckCircle, Clock, ArrowRight, DollarSign, BarChart3, Zap } from 'lucide-react';

// Mock data generators
const generatePriceData = () => {
  const data = [];
  let price = 100;
  for (let i = 0; i < 50; i++) {
    price += (Math.random() - 0.5) * 3;
    data.push({
      time: `${i}`,
      price: price,
      volume: Math.random() * 1000
    });
  }
  return data;
};

const generatePnLData = () => {
  const data = [];
  let value = 0;
  for (let i = 0; i < 24; i++) {
    value += (Math.random() - 0.45) * 2;
    data.push({
      time: `${i}:00`,
      pnl: value
    });
  }
  return data;
};

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [isTrading, setIsTrading] = useState(false);
  const [pnlInUSDT, setPnlInUSDT] = useState(false);
  const [selectedCoin, setSelectedCoin] = useState('BTC');
  const [showCoinSelector, setShowCoinSelector] = useState(false);
  
  // User data
  const [userData, setUserData] = useState({
    username: '',
    password: '',
    tradeType: '',
    strategy: '',
    exchanges: [],
    apiKeys: {}
  });

  // Trading parameters
  const [tradeParams, setTradeParams] = useState({
    side: 'LONG',
    stopLoss: 2,
    takeProfit: 5,
    frequency: 'medium',
    orderSize: 100
  });

  // Bot activity logs
  const [botLogs, setBotLogs] = useState([
    { id: 1, time: '10:23:45', type: 'search', message: 'Анализирую рынок, ищу точку входа...', status: 'active' },
    { id: 2, time: '10:22:10', type: 'success', message: 'Купил 10 SOL на Bybit по $142.50', status: 'completed' },
    { id: 3, time: '10:22:15', type: 'transfer', message: 'Перевожу 10 SOL: Bybit → Binance', status: 'completed' },
    { id: 4, time: '10:22:45', type: 'success', message: 'Продал 10 SOL на Binance по $143.20', status: 'completed' },
    { id: 5, time: '10:22:46', type: 'profit', message: 'Сделка завершена. Профит: +$7.00 (0.49%)', status: 'completed' }
  ]);

  // Active trades
  const [activeTrades, setActiveTrades] = useState([
    { id: 1, coin: 'BTC', type: 'Арбитраж', entry: 42150, current: 42280, pnl: 130, pnlPercent: 0.31, status: 'active' },
    { id: 2, coin: 'ETH', type: 'Арбитраж', entry: 2245, current: 2257, pnl: 12, pnlPercent: 0.53, status: 'active' }
  ]);

  // Market data
  const [balances, setBalances] = useState({
    binance: 10342.50,
    gateio: 9876.20,
    bybit: 10125.80
  });

  const [pnl, setPnl] = useState(342.50);
  const [pnlPercent, setPnlPercent] = useState(3.42);
  const [pnlData, setPnlData] = useState(generatePnLData());
  const [priceData, setPriceData] = useState(generatePriceData());

  // Available coins
  const coins = [
    { symbol: 'BTC', name: 'Bitcoin', price: 42280, change: 2.4 },
    { symbol: 'ETH', name: 'Ethereum', price: 2257, change: 1.8 },
    { symbol: 'SOL', name: 'Solana', price: 142.50, change: -0.5 },
    { symbol: 'BNB', name: 'BNB', price: 315.20, change: 0.9 },
    { symbol: 'XRP', name: 'Ripple', price: 0.52, change: 3.2 },
    { symbol: 'ADA', name: 'Cardano', price: 0.48, change: -1.1 }
  ];

  const tradeTypes = [
    {
      id: 'margin',
      name: 'Маржинальный трейдинг',
      strategies: [
        { id: 'breakout', name: 'Пробой уровня с подтверждением объёма' },
        { id: 'retest', name: 'Ретест ложного пробоя' },
        { id: 'trend', name: 'Торговля по тренду' }
      ]
    },
    {
      id: 'arbitrage',
      name: 'Арбитраж',
      strategies: [
        { id: 'inter-exchange', name: 'Межбиржевой арбитраж' },
        { id: 'triangular', name: 'Треугольный арбитраж' },
        { id: 'intra-exchange', name: 'Внутрибиржевой арбитраж' }
      ]
    }
  ];

  const exchanges = [
    { id: 'binance', name: 'Binance' },
    { id: 'gateio', name: 'Gate.io' },
    { id: 'bybit', name: 'Bybit' }
  ];

  // Simulate bot activity
  useEffect(() => {
    if (isTrading) {
      const interval = setInterval(() => {
        const actions = [
          { type: 'search', message: 'Анализирую спреды между биржами...', status: 'active' },
          { type: 'search', message: 'Обнаружена возможность арбитража на паре BTC/USDT', status: 'active' },
          { type: 'buy', message: `Купил 0.05 ${selectedCoin} на Gate.io по $${(Math.random() * 50000 + 40000).toFixed(2)}`, status: 'completed' },
          { type: 'transfer', message: `Перевожу ${selectedCoin}: Gate.io → Binance`, status: 'completed' },
          { type: 'sell', message: `Продал 0.05 ${selectedCoin} на Binance по $${(Math.random() * 50000 + 40100).toFixed(2)}`, status: 'completed' },
          { type: 'profit', message: `Сделка завершена. Профит: +$${(Math.random() * 20 + 5).toFixed(2)} (${(Math.random() * 0.5 + 0.1).toFixed(2)}%)`, status: 'completed' }
        ];
        
        const randomAction = actions[Math.floor(Math.random() * actions.length)];
        const newLog = {
          id: Date.now(),
          time: new Date().toLocaleTimeString('ru-RU'),
          ...randomAction
        };
        
        setBotLogs(prev => [newLog, ...prev.slice(0, 19)]);
        
        // Update PnL
        setPnl(prev => prev + (Math.random() * 10 - 4));
        setPnlPercent(prev => prev + (Math.random() * 0.2 - 0.08));
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [isTrading, selectedCoin]);

  const handleLogin = () => {
    if (userData.username && userData.password) {
      setIsAuthenticated(true);
      setShowSettings(true);
    }
  };

  const handleTradeTypeSelect = (typeId) => {
    setUserData({ ...userData, tradeType: typeId, strategy: '' });
  };

  const handleStrategySelect = (strategyId) => {
    setUserData({ ...userData, strategy: strategyId });
  };

  const handleExchangeToggle = (exchangeId) => {
    const newExchanges = userData.exchanges.includes(exchangeId)
      ? userData.exchanges.filter(id => id !== exchangeId)
      : [...userData.exchanges, exchangeId];
    
    if (newExchanges.length <= 3) {
      setUserData({ ...userData, exchanges: newExchanges });
    }
  };

  const handleApiKeyChange = (exchange, field, value) => {
    setUserData({
      ...userData,
      apiKeys: {
        ...userData.apiKeys,
        [exchange]: {
          ...userData.apiKeys[exchange],
          [field]: value
        }
      }
    });
  };

  const handleSaveSettings = () => {
    setShowSettings(false);
  };

  const toggleTrading = () => {
    setIsTrading(!isTrading);
    if (!isTrading) {
      setBotLogs([{
        id: Date.now(),
        time: new Date().toLocaleTimeString('ru-RU'),
        type: 'success',
        message: '🚀 Бот запущен! Начинаю мониторинг рынка...',
        status: 'active'
      }, ...botLogs]);
    } else {
      setBotLogs([{
        id: Date.now(),
        time: new Date().toLocaleTimeString('ru-RU'),
        type: 'info',
        message: '⏸️ Бот остановлен. Открытые позиции сохранены.',
        status: 'completed'
      }, ...botLogs]);
    }
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

  // Login Screen
  const LoginScreen = () => (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex items-center justify-center p-4">
      <div className="bg-gray-800/50 backdrop-blur-xl p-8 rounded-2xl shadow-2xl border border-gray-700 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-block p-3 bg-blue-500/20 rounded-xl mb-4">
            <TrendingUp className="w-12 h-12 text-blue-400" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">AutoFutures</h1>
          <p className="text-gray-400">Автоматизированная торговля криптовалютой</p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Логин</label>
            <input
              type="text"
              value={userData.username}
              onChange={(e) => setUserData({ ...userData, username: e.target.value })}
              className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition"
              placeholder="Введите логин"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Пароль</label>
            <input
              type="password"
              value={userData.password}
              onChange={(e) => setUserData({ ...userData, password: e.target.value })}
              className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition"
              placeholder="Введите пароль"
            />
          </div>

          <button
            onClick={handleLogin}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition transform hover:scale-105"
          >
            Войти
          </button>

          <button
            onClick={handleLogin}
            className="w-full py-3 bg-gray-700 hover:bg-gray-600 text-white font-semibold rounded-lg transition"
          >
            Регистрация
          </button>
        </div>
      </div>
    </div>
  );

  // Settings Screen
  const SettingsScreen = () => {
    const selectedTradeType = tradeTypes.find(t => t.id === userData.tradeType);

    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-4">
        <div className="max-w-4xl mx-auto py-8">
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-700 p-8">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-3xl font-bold text-white">Настройка торговли</h2>
              {!showSettings && (
                <button
                  onClick={() => setShowSettings(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              )}
            </div>

            <div className="mb-8">
              <h3 className="text-xl font-semibold text-white mb-4">Выберите вид торговли</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {tradeTypes.map(type => (
                  <button
                    key={type.id}
                    onClick={() => handleTradeTypeSelect(type.id)}
                    className={`p-6 rounded-xl border-2 transition transform hover:scale-105 ${
                      userData.tradeType === type.id
                        ? 'border-blue-500 bg-blue-500/20'
                        : 'border-gray-600 bg-gray-700/30 hover:border-gray-500'
                    }`}
                  >
                    <h4 className="text-lg font-semibold text-white">{type.name}</h4>
                  </button>
                ))}
              </div>
            </div>

            {userData.tradeType && selectedTradeType && (
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-white mb-4">Выберите стратегию</h3>
                <div className="space-y-3">
                  {selectedTradeType.strategies.map(strategy => (
                    <button
                      key={strategy.id}
                      onClick={() => handleStrategySelect(strategy.id)}
                      className={`w-full p-4 rounded-xl border-2 transition text-left ${
                        userData.strategy === strategy.id
                          ? 'border-blue-500 bg-blue-500/20'
                          : 'border-gray-600 bg-gray-700/30 hover:border-gray-500'
                      }`}
                    >
                      <span className="text-white">{strategy.name}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {userData.tradeType === 'arbitrage' && (
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-white mb-4">Выберите биржи (до 3-х)</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {exchanges.map(exchange => (
                    <button
                      key={exchange.id}
                      onClick={() => handleExchangeToggle(exchange.id)}
                      className={`p-4 rounded-xl border-2 transition ${
                        userData.exchanges.includes(exchange.id)
                          ? 'border-blue-500 bg-blue-500/20'
                          : 'border-gray-600 bg-gray-700/30 hover:border-gray-500'
                      }`}
                    >
                      <span className="text-white font-semibold">{exchange.name}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {userData.exchanges.length > 0 && (
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-white mb-4">API ключи</h3>
                <div className="space-y-6">
                  {userData.exchanges.map(exchangeId => {
                    const exchange = exchanges.find(e => e.id === exchangeId);
                    return (
                      <div key={exchangeId} className="bg-gray-700/30 p-6 rounded-xl border border-gray-600">
                        <h4 className="text-lg font-semibold text-white mb-4">{exchange.name}</h4>
                        <div className="space-y-3">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">API Key</label>
                            <input
                              type="text"
                              placeholder="Введите API ключ"
                              onChange={(e) => handleApiKeyChange(exchangeId, 'apiKey', e.target.value)}
                              className="w-full px-4 py-2 bg-gray-600/50 border border-gray-500 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">Secret Key</label>
                            <input
                              type="password"
                              placeholder="Введите секретный ключ"
                              onChange={(e) => handleApiKeyChange(exchangeId, 'secretKey', e.target.value)}
                              className="w-full px-4 py-2 bg-gray-600/50 border border-gray-500 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition"
                            />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <button
              onClick={handleSaveSettings}
              disabled={!userData.tradeType || !userData.strategy}
              className="w-full py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition transform hover:scale-105"
            >
              Сохранить и продолжить
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Dashboard Screen
  const DashboardScreen = () => {
    const selectedTradeType = tradeTypes.find(t => t.id === userData.tradeType);
    const selectedStrategy = selectedTradeType?.strategies.find(s => s.id === userData.strategy);
    const selectedCoinData = coins.find(c => c.symbol === selectedCoin);

    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
        {/* Header */}
        <div className="bg-gray-800/50 backdrop-blur-xl border-b border-gray-700">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <TrendingUp className="w-6 h-6 text-blue-400" />
              </div>
              <h1 className="text-2xl font-bold text-white">AutoFutures</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowSettings(true)}
                className="p-2 hover:bg-gray-700 rounded-lg transition"
              >
                <Settings className="w-5 h-5 text-gray-300" />
              </button>
              <button
                onClick={() => {
                  setIsAuthenticated(false);
                  setUserData({
                    username: '',
                    password: '',
                    tradeType: '',
                    strategy: '',
                    exchanges: [],
                    apiKeys: {}
                  });
                }}
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
              <div className="text-white font-semibold">{selectedTradeType?.name}</div>
              <div className="text-gray-300 text-xs mt-1">{selectedStrategy?.name}</div>
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
              <div className={`text-xl font-bold ${pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {pnl >= 0 ? '+' : ''}{pnlInUSDT ? `$${pnl.toFixed(2)}` : `${pnlPercent.toFixed(2)}%`}
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
              <div className="text-white font-bold text-xl">24</div>
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
                        onClick={() => {
                          setSelectedCoin(coin.symbol);
                          setShowCoinSelector(false);
                          setPriceData(generatePriceData());
                        }}
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
                      <div className="text-gray-400 text-sm">{selectedCoinData?.name}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold text-white">${selectedCoinData?.price.toLocaleString()}</div>
                      <div className={`text-sm font-semibold ${selectedCoinData?.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {selectedCoinData?.change >= 0 ? '+' : ''}{selectedCoinData?.change}%
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
                  {activeTrades.length > 0 ? activeTrades.map(trade => (
                    <div key={trade.id} className="bg-gray-700/30 p-4 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <BarChart3 className="w-4 h-4 text-blue-400" />
                          <span className="text-white font-semibold">{trade.coin}/USDT</span>
                          <span className="text-xs text-gray-400">{trade.type}</span>
                        </div>
                        <div className={`text-sm font-bold ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <div className="text-gray-400 text-xs">Вход</div>
                          <div className="text-white">${trade.entry}</div>
                        </div>
                        <div>
                          <div className="text-gray-400 text-xs">Текущая</div>
                          <div className="text-white">${trade.current}</div>
                        </div>
                        <div>
                          <div className="text-gray-400 text-xs">PnL</div>
                          <div className={`font-semibold ${trade.pnlPercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {trade.pnlPercent >= 0 ? '+' : ''}{trade.pnlPercent}%
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

            {/* Right Column - Controls and Logs */}
            <div className="space-y-6">
              {/* Trading Controls */}
              <div className="bg-gray-800/50 backdrop-blur-xl p-6 rounded-xl border border-gray-700">
                <h3 className="text-lg font-semibold text-white mb-4">Управление</h3>
                
                <button
                  onClick={toggleTrading}
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
                        onClick={() => setTradeParams({ ...tradeParams, side: 'LONG' })}
                        className={`py-2 rounded-lg transition text-sm font-semibold ${
                          tradeParams.side === 'LONG'
                            ? 'bg-green-600 text-white'
                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                        }`}
                      >
                        LONG
                      </button>
                      <button
                        onClick={() => setTradeParams({ ...tradeParams, side: 'SHORT' })}
                        className={`py-2 rounded-lg transition text-sm font-semibold ${
                          tradeParams.side === 'SHORT'
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
                      value={tradeParams.orderSize}
                      onChange={(e) => setTradeParams({ ...tradeParams, orderSize: parseFloat(e.target.value) })}
                      className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Stop Loss (%)</label>
                    <input
                      type="number"
                      value={tradeParams.stopLoss}
                      onChange={(e) => setTradeParams({ ...tradeParams, stopLoss: parseFloat(e.target.value) })}
                      className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Take Profit (%)</label>
                    <input
                      type="number"
                      value={tradeParams.takeProfit}
                      onChange={(e) => setTradeParams({ ...tradeParams, takeProfit: parseFloat(e.target.value) })}
                      className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Частота сделок</label>
                    <select
                      value={tradeParams.frequency}
                      onChange={(e) => setTradeParams({ ...tradeParams, frequency: e.target.value })}
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
                  {userData.exchanges.map(exchangeId => {
                    const exchange = exchanges.find(e => e.id === exchangeId);
                    return (
                      <div key={exchangeId} className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg">
                        <span className="text-white text-sm font-medium">{exchange.name}</span>
                        <span className="text-green-400 font-semibold text-sm">${balances[exchangeId]?.toFixed(2)}</span>
                      </div>
                    );
                  })}
                  <div className="pt-3 border-t border-gray-600">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-300 text-sm font-medium">Всего</span>
                      <span className="text-white font-bold">
                        ${Object.values(balances).reduce((a, b) => a + b, 0).toFixed(2)}
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
              {botLogs.map((log) => (
                <div
                  key={log.id}
                  className={`p-4 rounded-lg border transition-all ${
                    log.status === 'active'
                      ? 'bg-blue-500/10 border-blue-500/30'
                      : 'bg-gray-700/30 border-gray-600/30'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <div className="mt-0.5">{getLogIcon(log.type)}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-gray-400 font-mono">{log.time}</span>
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
              ))}
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

  // Main render logic
  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  if (showSettings) {
    return <SettingsScreen />;
  }

  return <DashboardScreen />;
};

export default App;
