-- backend/database/init.sql
-- Скрипт инициализации базы данных MySQL для AutoFutures

CREATE DATABASE IF NOT EXISTS autofutures CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE autofutures;

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица настроек пользователей
CREATE TABLE IF NOT EXISTS user_settings (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    trade_type ENUM('margin', 'arbitrage') NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    telegram_notifications BOOLEAN DEFAULT FALSE,
    telegram_chat_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица подключений к биржам
CREATE TABLE IF NOT EXISTS exchange_connections (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    exchange_id VARCHAR(20) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    secret_key_encrypted TEXT NOT NULL,
    passphrase_encrypted TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_sync TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_exchange (user_id, exchange_id),
    INDEX idx_user_id (user_id),
    INDEX idx_exchange_id (exchange_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица сделок
CREATE TABLE IF NOT EXISTS trades (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    trade_type ENUM('arbitrage', 'margin', 'spot') NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side ENUM('buy', 'sell', 'long', 'short') NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    exit_price DECIMAL(20, 8),
    amount DECIMAL(20, 8) NOT NULL,
    filled_amount DECIMAL(20, 8) DEFAULT 0,
    pnl DECIMAL(20, 8),
    pnl_percent DECIMAL(10, 4),
    fees DECIMAL(20, 8) DEFAULT 0,
    status ENUM('pending', 'active', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
    exchanges JSON,  -- список бирж для арбитража
    strategy VARCHAR(50),
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_symbol (symbol),
    INDEX idx_status (status),
    INDEX idx_opened_at (opened_at),
    INDEX idx_closed_at (closed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица ордеров
CREATE TABLE IF NOT EXISTS orders (
    id VARCHAR(36) PRIMARY KEY,
    trade_id VARCHAR(36),
    user_id VARCHAR(36) NOT NULL,
    exchange_id VARCHAR(20) NOT NULL,
    exchange_order_id VARCHAR(100),
    symbol VARCHAR(20) NOT NULL,
    order_type ENUM('market', 'limit', 'stop_loss', 'take_profit') NOT NULL,
    side ENUM('buy', 'sell') NOT NULL,
    price DECIMAL(20, 8),
    amount DECIMAL(20, 8) NOT NULL,
    filled_amount DECIMAL(20, 8) DEFAULT 0,
    status ENUM('pending', 'open', 'filled', 'cancelled', 'failed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    filled_at TIMESTAMP NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_trade_id (trade_id),
    INDEX idx_exchange_id (exchange_id),
    INDEX idx_status (status),
    INDEX idx_exchange_order_id (exchange_order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица балансов
CREATE TABLE IF NOT EXISTS balances (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    exchange_id VARCHAR(20) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    free_balance DECIMAL(20, 8) DEFAULT 0,
    locked_balance DECIMAL(20, 8) DEFAULT 0,
    total_balance DECIMAL(20, 8) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_balance (user_id, exchange_id, currency),
    INDEX idx_user_id (user_id),
    INDEX idx_exchange_id (exchange_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица логов бота
CREATE TABLE IF NOT EXISTS bot_logs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    trade_id VARCHAR(36),
    log_type ENUM('info', 'success', 'error', 'warning', 'search', 'buy', 'sell', 'transfer', 'profit') NOT NULL,
    message TEXT NOT NULL,
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_log_type (log_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица PnL истории
CREATE TABLE IF NOT EXISTS pnl_history (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    pnl DECIMAL(20, 8) NOT NULL,
    pnl_percent DECIMAL(10, 4) NOT NULL,
    cumulative_pnl DECIMAL(20, 8) NOT NULL,
    trades_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица уведомлений
CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type ENUM('info', 'success', 'warning', 'error') NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_is_read (is_read),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица сессий (для JWT токенов)
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица параметров стратегий
CREATE TABLE IF NOT EXISTS strategy_parameters (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    strategy_type VARCHAR(50) NOT NULL,
    parameters JSON NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_strategy_type (strategy_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Представления для аналитики

-- Статистика по сделкам пользователя
CREATE OR REPLACE VIEW user_trade_statistics AS
SELECT 
    user_id,
    COUNT(*) as total_trades,
    SUM(CASE WHEN status = 'completed' AND pnl > 0 THEN 1 ELSE 0 END) as successful_trades,
    SUM(CASE WHEN status = 'completed' AND pnl < 0 THEN 1 ELSE 0 END) as failed_trades,
    SUM(CASE WHEN status = 'completed' AND pnl > 0 THEN 1 ELSE 0 END) / COUNT(*) * 100 as win_rate,
    SUM(CASE WHEN status = 'completed' THEN pnl ELSE 0 END) as total_pnl,
    AVG(CASE WHEN status = 'completed' THEN pnl_percent ELSE NULL END) as avg_pnl_percent,
    MAX(pnl) as best_trade,
    MIN(pnl) as worst_trade,
    AVG(TIMESTAMPDIFF(MINUTE, opened_at, closed_at)) as avg_trade_duration_minutes
FROM trades
WHERE status = 'completed'
GROUP BY user_id;

-- Дневная статистика
CREATE OR REPLACE VIEW daily_statistics AS
SELECT 
    user_id,
    DATE(closed_at) as trade_date,
    COUNT(*) as trades_count,
    SUM(pnl) as daily_pnl,
    AVG(pnl_percent) as avg_pnl_percent
FROM trades
WHERE status = 'completed' AND closed_at IS NOT NULL
GROUP BY user_id, DATE(closed_at);

-- Создание тестового пользователя (опционально, для разработки)
-- INSERT INTO users (id, username, email, password_hash) 
-- VALUES (
--     UUID(),
--     'testuser',
--     'test@example.com',
--     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeP8RiZKqJE6'  -- пароль: password123
-- );

-- Процедуры для очистки старых данных

DELIMITER //

-- Удаление истекших сессий
CREATE PROCEDURE clean_expired_sessions()
BEGIN
    DELETE FROM sessions WHERE expires_at < NOW();
END //

-- Удаление старых логов (старше 30 дней)
CREATE PROCEDURE clean_old_logs()
BEGIN
    DELETE FROM bot_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
END //

-- Архивация старых сделок
CREATE PROCEDURE archive_old_trades()
BEGIN
    -- Можно создать архивную таблицу и переносить туда старые сделки
    DELETE FROM trades WHERE closed_at < DATE_SUB(NOW(), INTERVAL 90 DAY) AND status = 'completed';
END //

DELIMITER ;

-- Создание событий для автоматической очистки
CREATE EVENT IF NOT EXISTS clean_expired_sessions_event
ON SCHEDULE EVERY 1 HOUR
DO CALL clean_expired_sessions();

CREATE EVENT IF NOT EXISTS clean_old_logs_event
ON SCHEDULE EVERY 1 DAY
DO CALL clean_old_logs();

-- Индексы для производительности
CREATE INDEX idx_trades_user_status ON trades(user_id, status);
CREATE INDEX idx_trades_user_opened ON trades(user_id, opened_at DESC);
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- Комментарии к таблицам
ALTER TABLE users COMMENT = 'Таблица пользователей системы';
ALTER TABLE trades COMMENT = 'Основная таблица сделок';
ALTER TABLE orders COMMENT = 'Ордера на биржах';
ALTER TABLE bot_logs COMMENT = 'Логи активности торгового бота';
ALTER TABLE balances COMMENT = 'Балансы пользователей на биржах';

-- Проверка целостности данных
-- Добавляем триггеры для автоматического обновления

DELIMITER //

-- Триггер для обновления PnL в сделке
CREATE TRIGGER update_trade_pnl 
BEFORE UPDATE ON trades
FOR EACH ROW
BEGIN
    IF NEW.exit_price IS NOT NULL AND NEW.entry_price IS NOT NULL THEN
        IF NEW.side IN ('buy', 'long') THEN
            SET NEW.pnl = (NEW.exit_price - NEW.entry_price) * NEW.filled_amount;
            SET NEW.pnl_percent = ((NEW.exit_price - NEW.entry_price) / NEW.entry_price) * 100;
        ELSE
            SET NEW.pnl = (NEW.entry_price - NEW.exit_price) * NEW.filled_amount;
            SET NEW.pnl_percent = ((NEW.entry_price - NEW.exit_price) / NEW.entry_price) * 100;
        END IF;
    END IF;
END //

-- Триггер для обновления last_activity в sessions
CREATE TRIGGER update_session_activity
BEFORE UPDATE ON sessions
FOR EACH ROW
BEGIN
    SET NEW.last_activity = CURRENT_TIMESTAMP;
END //

DELIMITER ;

-- Успешная инициализация базы данных
SELECT 'Database initialized successfully!' as message;
