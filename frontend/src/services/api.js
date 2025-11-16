// frontend/src/services/api.js - ПОЛНОСТЬЮ ИСПРАВЛЕНО
const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host;

class ApiService {
  constructor() {
    this.token = localStorage.getItem('token');
    this.user_id = localStorage.getItem('user_id'); // ДОБАВЛЕНО
    this.ws = null;
  }

  async fetchWithAuth(url, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Token ${this.token}`; // Правильный формат
    }

    const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;

    const response = await fetch(fullUrl, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'API Error' }));
      throw new Error(error.detail || 'API Error');
    }

    return response.json();
  }

  // ==================== AUTH ====================
  async register(username, password, email) {
    const data = await this.fetchWithAuth('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, email }),
    });
    this.token = data.token;
    this.user_id = data.user_id; // СОХРАНЯЕМ USER_ID
    localStorage.setItem('token', data.token);
    localStorage.setItem('user_id', data.user_id);
    return data;
  }

  async login(username, password) {
    const data = await this.fetchWithAuth('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    this.token = data.token;
    this.user_id = data.user_id; // СОХРАНЯЕМ USER_ID
    localStorage.setItem('token', data.token);
    localStorage.setItem('user_id', data.user_id);
    return data;
  }

  logout() {
    this.token = null;
    this.user_id = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // ==================== USER ====================
  async getProfile() {
    return this.fetchWithAuth('/api/user/profile');
  }

  async getSettings() {
    return this.fetchWithAuth('/api/user/settings');
  }

  async saveSettings(settings) {
    return this.fetchWithAuth('/api/user/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  }

  // ==================== EXCHANGES ====================
  async connectExchange(exchangeId, apiKey, secretKey, passphrase = null) {
    return this.fetchWithAuth('/api/exchanges/connect', {
      method: 'POST',
      body: JSON.stringify({
        exchange_id: exchangeId,
        api_key: apiKey,
        secret_key: secretKey,
        passphrase: passphrase,
      }),
    });
  }

  async getBalances() {
    return this.fetchWithAuth('/api/exchanges/balances');
  }

  async getSupportedExchanges() {
    return this.fetchWithAuth('/api/exchanges/supported');
  }

  // ==================== ARBITRAGE ====================
  async analyzeArbitrage(coin, exchangeFrom, exchangeTo, orderSize = 100) {
    return this.fetchWithAuth('/api/arbitrage/analyze', {
      method: 'POST',
      body: JSON.stringify({
        coin,
        exchange_from: exchangeFrom,
        exchange_to: exchangeTo,
        order_size: orderSize,
      }),
    });
  }

  async scanArbitrage(coins, exchanges, minProfitPercent = 0.5, orderSize = 100) {
    return this.fetchWithAuth('/api/arbitrage/scan', {
      method: 'POST',
      body: JSON.stringify({
        coins,
        exchanges,
        min_profit_percent: minProfitPercent,
        order_size: orderSize,
      }),
    });
  }

  async calculateProfit(params) {
    return this.fetchWithAuth('/api/arbitrage/calculate-profit', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // ==================== TRADING ====================
  async startTrading(params) {
    return this.fetchWithAuth('/api/trading/start', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async stopTrading() {
    return this.fetchWithAuth('/api/trading/stop', {
      method: 'POST',
    });
  }

  async getTradeStatus() {
    return this.fetchWithAuth('/api/trading/status');
  }

  async getActiveTrades() {
    return this.fetchWithAuth('/api/trading/active');
  }

  async getTradeHistory(limit = 100) {
    return this.fetchWithAuth(`/api/trading/history?limit=${limit}`);
  }

  async getBotLogs(limit = 50) {
    return this.fetchWithAuth(`/api/trading/logs?limit=${limit}`);
  }

  // ==================== MARKET DATA ====================
  async getTopCoins(limit = 10) {
    return this.fetchWithAuth(`/api/market/top-coins?limit=${limit}`);
  }

  async getPriceHistory(symbol, interval = '1m', limit = 100) {
    return this.fetchWithAuth(`/api/market/price-history/${symbol}?interval=${interval}&limit=${limit}`);
  }

  // ==================== ANALYTICS ====================
  async getPnLData(period = '24h') {
    return this.fetchWithAuth(`/api/analytics/pnl?period=${period}`);
  }

  async getStatistics() {
    return this.fetchWithAuth('/api/analytics/statistics');
  }

  // ==================== WEBSOCKET - ИСПРАВЛЕНО ====================
  connectWebSocket(onMessage, onError = null) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return this.ws;
    }

    // ИСПРАВЛЕНО: используем user_id, убираем дублирование /ws/
    if (!this.user_id) {
      console.error('Cannot connect WebSocket: user_id not found');
      return null;
    }

    const wsUrl = `${WS_BASE_URL}/ws/${this.user_id}`;
    console.log('Connecting to WebSocket:', wsUrl);

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.ws.send(JSON.stringify({ type: 'subscribe', user_id: this.user_id }));
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) onError(error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Reconnect after 5 seconds
      setTimeout(() => {
        if (this.token && this.user_id) {
          this.connectWebSocket(onMessage, onError);
        }
      }, 5000);
    };

    return this.ws;
  }

  disconnectWebSocket() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // ==================== HEALTH ====================
  async healthCheck() {
    return this.fetchWithAuth('/health/');
  }
}

export default new ApiService();
