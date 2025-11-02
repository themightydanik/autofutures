// frontend/src/components/SettingsScreen.jsx
import React, { useState, useEffect } from 'react';
import { X, CheckCircle, AlertCircle } from 'lucide-react';
import { useTrading } from '../context/TradingContext';

const SettingsScreen = ({ onComplete }) => {
  const { settings, saveSettings, connectExchange } = useTrading();
  
  const [formData, setFormData] = useState({
    trade_type: '',
    strategy: '',
    exchanges: []
  });
  
  const [apiKeys, setApiKeys] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (settings) {
      setFormData({
        trade_type: settings.trade_type || '',
        strategy: settings.strategy || '',
        exchanges: settings.exchanges || []
      });
    }
  }, [settings]);

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

  const handleTradeTypeSelect = (typeId) => {
    setFormData({ ...formData, trade_type: typeId, strategy: '' });
  };

  const handleStrategySelect = (strategyId) => {
    setFormData({ ...formData, strategy: strategyId });
  };

  const handleExchangeToggle = (exchangeId) => {
    const newExchanges = formData.exchanges.includes(exchangeId)
      ? formData.exchanges.filter(id => id !== exchangeId)
      : [...formData.exchanges, exchangeId];
    
    if (newExchanges.length <= 3) {
      setFormData({ ...formData, exchanges: newExchanges });
    }
  };

  const handleApiKeyChange = (exchange, field, value) => {
    setApiKeys({
      ...apiKeys,
      [exchange]: {
        ...apiKeys[exchange],
        [field]: value
      }
    });
  };

  const handleSaveSettings = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Save basic settings
      const result = await saveSettings(formData);
      
      if (!result.success) {
        setError(result.error || 'Ошибка сохранения настроек');
        setLoading(false);
        return;
      }

      // Connect exchanges with API keys
      for (const exchangeId of formData.exchanges) {
        const keys = apiKeys[exchangeId];
        if (keys?.apiKey && keys?.secretKey) {
          try {
            await connectExchange(exchangeId, keys.apiKey, keys.secretKey, keys.passphrase);
          } catch (err) {
            console.error(`Failed to connect ${exchangeId}:`, err);
          }
        }
      }

      setSuccess('Настройки сохранены успешно!');
      setTimeout(() => {
        onComplete();
      }, 1500);
    } catch (err) {
      setError(err.message || 'Произошла ошибка');
    } finally {
      setLoading(false);
    }
  };

  const selectedTradeType = tradeTypes.find(t => t.id === formData.trade_type);
  const canSave = formData.trade_type && formData.strategy;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-4">
      <div className="max-w-4xl mx-auto py-8">
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-700 p-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-3xl font-bold text-white">Настройка торговли</h2>
            {settings?.trade_type && (
              <button
                onClick={onComplete}
                className="text-gray-400 hover:text-white transition"
              >
                <X className="w-6 h-6" />
              </button>
            )}
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 bg-green-500/20 border border-green-500/50 rounded-lg flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <p className="text-green-300 text-sm">{success}</p>
            </div>
          )}

          {/* Trade Type Selection */}
          <div className="mb-8">
            <h3 className="text-xl font-semibold text-white mb-4">Выберите вид торговли</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {tradeTypes.map(type => (
                <button
                  key={type.id}
                  onClick={() => handleTradeTypeSelect(type.id)}
                  className={`p-6 rounded-xl border-2 transition transform hover:scale-105 ${
                    formData.trade_type === type.id
                      ? 'border-blue-500 bg-blue-500/20'
                      : 'border-gray-600 bg-gray-700/30 hover:border-gray-500'
                  }`}
                >
                  <h4 className="text-lg font-semibold text-white">{type.name}</h4>
                </button>
              ))}
            </div>
          </div>

          {/* Strategy Selection */}
          {formData.trade_type && selectedTradeType && (
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-white mb-4">Выберите стратегию</h3>
              <div className="space-y-3">
                {selectedTradeType.strategies.map(strategy => (
                  <button
                    key={strategy.id}
                    onClick={() => handleStrategySelect(strategy.id)}
                    className={`w-full p-4 rounded-xl border-2 transition text-left ${
                      formData.strategy === strategy.id
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

          {/* Exchange Selection for Arbitrage */}
          {formData.trade_type === 'arbitrage' && (
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-white mb-4">
                Выберите биржи (до 3-х)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {exchanges.map(exchange => (
                  <button
                    key={exchange.id}
                    onClick={() => handleExchangeToggle(exchange.id)}
                    disabled={!formData.exchanges.includes(exchange.id) && formData.exchanges.length >= 3}
                    className={`p-4 rounded-xl border-2 transition ${
                      formData.exchanges.includes(exchange.id)
                        ? 'border-blue-500 bg-blue-500/20'
                        : 'border-gray-600 bg-gray-700/30 hover:border-gray-500 disabled:opacity-50 disabled:cursor-not-allowed'
                    }`}
                  >
                    <span className="text-white font-semibold">{exchange.name}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* API Keys Input */}
          {formData.exchanges.length > 0 && (
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-white mb-4">API ключи</h3>
              <p className="text-gray-400 text-sm mb-4">
                API ключи шифруются и хранятся безопасно
              </p>
              <div className="space-y-6">
                {formData.exchanges.map(exchangeId => {
                  const exchange = exchanges.find(e => e.id === exchangeId);
                  return (
                    <div key={exchangeId} className="bg-gray-700/30 p-6 rounded-xl border border-gray-600">
                      <h4 className="text-lg font-semibold text-white mb-4">{exchange.name}</h4>
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            API Key
                          </label>
                          <input
                            type="text"
                            placeholder="Введите API ключ"
                            onChange={(e) => handleApiKeyChange(exchangeId, 'apiKey', e.target.value)}
                            className="w-full px-4 py-2 bg-gray-600/50 border border-gray-500 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            Secret Key
                          </label>
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

          {/* Save Button */}
          <button
            onClick={handleSaveSettings}
            disabled={!canSave || loading}
            className="w-full py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition transform hover:scale-105 disabled:transform-none"
          >
            {loading ? 'Сохранение...' : 'Сохранить и продолжить'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsScreen;
