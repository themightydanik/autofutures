// frontend/src/services/api.js

const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const WS_BASE_URL =
  import.meta.env.VITE_WS_URL ||
  (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host;

class ApiService {
  constructor() {
    this.token = localStorage.getItem('token');
    this.ws = null;
  }

  // =============== Helper for authorized requests ===============
  async fetchWithAuth(url, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      // DRF TokenAuthentication format:
      headers['Authorization'] = `Token ${this.token}`;
    }

    const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;

    const response = await fetch(fullUrl, { ...options, headers });

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
    localStorage.setItem('token', data.token);
    return data;
  }

  async login(username, password) {
    const data = await this.fetchWithAuth('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });

    this.token = data.token;
    localStorage.setItem('token', data.token);
    return data;
  }

  async googleLogin(token) {
    const data = await this.fetchWithAuth('/api/auth/google', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });

    this.token = data.token;
    localStorage.setItem('token', data.token);
    return data;
  }

  logout() {
    this.token = null;
    localStorage.removeItem('token');
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
        passphrase,
      }),
    });
  }

  async getBalances() {
    return this.fetchWithAuth('/api/exchanges/balances');
  }

  async getAvailableCoins(exchangeId) {
    return this.fetchWithAuth(`/api/exchanges/available-coins?exchange_id=${exchangeId}`);
  }

  async getSupportedExchanges() {
    return this.fetchWithAuth('/api/exchanges/supported');
  }

  // ==================== TRADING ====================
  async startTrading(params) {
    return this.fetchWithAuth('/api/trade/start', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async stopTrading() {
    return this.fetchWithAuth('/api/trade/stop', { method: 'POST' });
  }

  async getTradeStatus() {
    return this.fetchWithAuth('/api/trade/status');
  }

  async updateParameters(params) {
    return this.fetchWithAuth('/api/trade/parameters', {
      method: 'PUT',
      body: JSON.stringify(params),
    });
  }

  async getActiveTrades() {
    return this.fetchWithAuth('/api/trade/active');
  }

  async getTradeHistory(limit = 100) {
    return this.fetchWithAuth(`/api/trade/history?limit=${limit}`);
  }

  async getBotLogs(limit = 50) {
    return this.fetchWithAuth(`/api/trade/logs?limit=${limit}`);
  }

  // ==================== MARKET DATA ====================
  async getPrice(exchangeId, symbol) {
    return this.fetchWithAuth(`/api/market/price/${exchangeId}/${symbol}`);
  }

  async getPriceHistory(symbol, interval = '1m', limit = 100) {
    return this.fetchWithAuth(
      `/api/market/price-history/${symbol}?interval=${interval}&limit=${limit}`
    );
  }

  async getTopCoins(limit = 10) {
    return this.fetchWithAuth(`/api/market/top-coins?limit=${limit}`);
  }

  // ==================== ANALYTICS ====================
  async getPnLData(period = '24h') {
    return this.fetchWithAuth(`/api/analytics/pnl?period=${period}`);
  }

  async getStatistics() {
    return this.fetchWithAuth('/api/analytics/statistics');
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

  async checkNetworkStatus(exchangeId, coin) {
    return this.fetchWithAuth(`/api/exchanges/${exchangeId}/network-status/${coin}`);
  }

  // ==================== WEBSOCKET ====================
  connectWebSocket(userId, onMessage, onError = null) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return this.ws;
    }

    const wsUrl = `${WS_BASE_URL}/ws/${userId}`;
    console.log('Connecting to WebSocket:', wsUrl);

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.ws.send(JSON.stringify({ type: 'subscribe', user_id: userId }));
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
      setTimeout(() => {
        if (this.token) {
          this.connectWebSocket(userId, onMessage, onError);
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
    return this.fetchWithAuth('/health');
  }
}

export default new ApiService();
