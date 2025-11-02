// frontend/src/App.jsx - Полностью интегрированный с бэкендом
import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { TradingProvider, useTrading } from './context/TradingContext';
import LoginScreen from './components/LoginScreen';
import SettingsScreen from './components/SettingsScreen';
import DashboardScreen from './components/DashboardScreen';

// Loading screen component
const LoadingScreen = () => (
  <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex items-center justify-center">
    <div className="text-center">
      <div className="inline-block p-4 bg-blue-500/20 rounded-xl mb-4 animate-pulse">
        <div className="w-16 h-16 border-4 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
      </div>
      <p className="text-white text-lg">Загрузка...</p>
    </div>
  </div>
);

// Main app content
const AppContent = () => {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { settings } = useTrading();
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    // Show settings if user hasn't configured them yet
    if (isAuthenticated && (!settings || !settings.trade_type || !settings.strategy)) {
      setShowSettings(true);
    }
  }, [isAuthenticated, settings]);

  if (authLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  if (showSettings || !settings?.trade_type) {
    return <SettingsScreen onComplete={() => setShowSettings(false)} />;
  }

  return <DashboardScreen onOpenSettings={() => setShowSettings(true)} />;
};

// Root App component with providers
const App = () => {
  return (
    <AuthProvider>
      <TradingProvider>
        <AppContent />
      </TradingProvider>
    </AuthProvider>
  );
};

export default App;
