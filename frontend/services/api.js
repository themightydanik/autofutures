// frontend/src/services/api.js

// В production URL будут относительными (через nginx proxy)
// В development можно указать полный URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host;

class ApiService {
  constructor() {
    this.token = localStorage.getItem('token');
    this.ws = null;
  }

  // Helper method for fetch with auth
  async fetchWithAuth(url, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
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

  // Auth methods
  async register(username, password) {
    const data = await this.fetchWithAuth('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
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

  logout() {
    this.token = null;
    localStorage.removeItem('token');
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // User settings
  async getSettings() {
    return this.fetchWithAuth('/api/user/settings');
  }

  async saveSettings(settings) {
    return this.fetchWithAuth('/api/user/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  }

  // Exchange methods
  async connectExchange(exchangeId, apiKey, secretKey) {
    return this.fetchWithAuth('/api/exchanges/connect', {
      method: 'POST',
      body: JSON.stringify({
        exchange_id: exchangeId,
        api_key: apiKey,
        secret_key: secretKey,
      }),
    });
  }

  async getBalances() {
    return this.fetchWithAuth('/api/exchanges/balances');
  }

  async getPrice(exchangeId, symbol) {
    return this.fetchWithAuth(`/api/exchanges/${exchangeId}/price/${symbol}`);
  }

  // Trading methods
  async startTrading(params) {
    return this.fetchWithAuth('/api/trade/start', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async stopTrading() {
    return this.fetchWithAuth('/api/trade/stop', {
      method: 'POST',
    });
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

  // Analytics
  async getPnLData(period = '24h') {
    return this.fetchWithAuth(`/api/analytics/pnl?period=${period}`);
  }

  async getStatistics() {
    return this.fetchWithAuth('/api/analytics/statistics');
  }

  // Market data
  async getPriceHistory(symbol, interval = '1m', limit = 100) {
    return this.fetchWithAuth(`/api/market/price-history/${symbol}?interval=${interval}&limit=${limit}`);
  }

  async getTopCoins(limit = 10) {
    return this.fetchWithAuth(`/api/market/top-coins?limit=${limit}`);
  }

  // WebSocket connection
  connectWebSocket(userId, onMessage, onError = null) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    // Формируем WebSocket URL
    const wsUrl = `${WS_BASE_URL}/ws/${userId}`;
    console.log('Connecting to WebSocket:', wsUrl);

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      // Subscribe to updates
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
      // Reconnect after 5 seconds
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
}

export default new ApiService();
