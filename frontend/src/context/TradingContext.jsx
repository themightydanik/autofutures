// frontend/src/context/TradingContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from './AuthContext';

const TradingContext = createContext(null);

export const TradingProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [isTrading, setIsTrading] = useState(false);
  const [settings, setSettings] = useState(null);
  const [tradeParams, setTradeParams] = useState({
    coin: 'BTC',
    side: 'LONG',
    order_size: 100.0,
    stop_loss: 2.0,
    take_profit: 5.0,
    frequency: 'medium'
  });
  const [activeTrades, setActiveTrades] = useState([]);
  const [tradeHistory, setTradeHistory] = useState([]);
  const [botLogs, setBotLogs] = useState([]);
  const [balances, setBalances] = useState({});
  const [pnl, setPnl] = useState({ total: 0, percent: 0 });
  const [ws, setWs] = useState(null);

  // Load initial data
  useEffect(() => {
    if (isAuthenticated && user) {
      loadSettings();
      loadBalances();
      loadActiveTrades();
      checkTradingStatus();
    }
  }, [isAuthenticated, user]);

  // WebSocket connection
  useEffect(() => {
    if (isAuthenticated && user) {
      const websocket = api.connectWebSocket(
        user.user_id,
        handleWebSocketMessage,
        handleWebSocketError
      );
      setWs(websocket);

      return () => {
        if (websocket) {
          api.disconnectWebSocket();
        }
      };
    }
  }, [isAuthenticated, user]);

  const handleWebSocketMessage = (data) => {
    console.log('WebSocket message:', data);
    
    if (data.type === 'update') {
      // Update real-time data
      if (data.data.pnl !== undefined) {
        setPnl({
          total: data.data.pnl,
          percent: data.data.pnl_percent
        });
      }
      if (data.data.active_trades) {
        setActiveTrades(data.data.active_trades);
      }
      if (data.data.latest_logs) {
        setBotLogs(prev => [...data.data.latest_logs, ...prev].slice(0, 50));
      }
      if (data.data.is_running !== undefined) {
        setIsTrading(data.data.is_running);
      }
    } else if (data.type === 'log') {
      // New log message
      setBotLogs(prev => [data.data, ...prev].slice(0, 50));
    } else if (data.type === 'trade') {
      // New trade
      setActiveTrades(prev => [data.data, ...prev]);
    }
  };

  const handleWebSocketError = (error) => {
    console.error('WebSocket error:', error);
  };

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      setSettings(data);
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const saveSettings = async (newSettings) => {
    try {
      await api.saveSettings(newSettings);
      setSettings(newSettings);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const loadBalances = async () => {
    try {
      const data = await api.getBalances();
      setBalances(data);
    } catch (error) {
      console.error('Failed to load balances:', error);
    }
  };

  const loadActiveTrades = async () => {
    try {
      const trades = await api.getActiveTrades();
      setActiveTrades(trades);
    } catch (error) {
      console.error('Failed to load active trades:', error);
    }
  };

  const loadTradeHistory = async (limit = 100) => {
    try {
      const history = await api.getTradeHistory(limit);
      setTradeHistory(history);
    } catch (error) {
      console.error('Failed to load trade history:', error);
    }
  };

  const checkTradingStatus = async () => {
    try {
      const status = await api.getTradeStatus();
      setIsTrading(status.is_running);
    } catch (error) {
      console.error('Failed to check trading status:', error);
    }
  };

  const startTrading = async (params) => {
    try {
      await api.startTrading(params || tradeParams);
      setIsTrading(true);
      setBotLogs(prev => [{
        id: Date.now(),
        time: new Date().toLocaleTimeString('ru-RU'),
        type: 'success',
        message: '🚀 Бот запущен! Начинаю мониторинг рынка...',
        status: 'active'
      }, ...prev]);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const stopTrading = async () => {
    try {
      await api.stopTrading();
      setIsTrading(false);
      setBotLogs(prev => [{
        id: Date.now(),
        time: new Date().toLocaleTimeString('ru-RU'),
        type: 'info',
        message: '⏸️ Бот остановлен. Открытые позиции сохранены.',
        status: 'completed'
      }, ...prev]);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const updateTradeParams = async (params) => {
    try {
      await api.updateParameters(params);
      setTradeParams(params);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const connectExchange = async (exchangeId, apiKey, secretKey, passphrase) => {
    try {
      await api.connectExchange(exchangeId, apiKey, secretKey, passphrase);
      await loadBalances();
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const value = {
    isTrading,
    settings,
    tradeParams,
    activeTrades,
    tradeHistory,
    botLogs,
    balances,
    pnl,
    setTradeParams,
    saveSettings,
    startTrading,
    stopTrading,
    updateTradeParams,
    connectExchange,
    loadBalances,
    loadActiveTrades,
    loadTradeHistory,
    refreshSettings: loadSettings
  };

  return (
    <TradingContext.Provider value={value}>
      {children}
    </TradingContext.Provider>
  );
};

export const useTrading = () => {
  const context = useContext(TradingContext);
  if (!context) {
    throw new Error('useTrading must be used within TradingProvider');
  }
  return context;
};
