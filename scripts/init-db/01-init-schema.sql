-- init-db/01-init-schema.sql
-- Создание таблиц, соответствующих коллекциям Firestore

-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name TEXT,
    email TEXT,
    gender VARCHAR(10),
    age INTEGER,
    height FLOAT,
    current_weight FLOAT,
    target_weight FLOAT,
    activity_level VARCHAR(20),
    weight_goal VARCHAR(10),
    diet_preference VARCHAR(20),
    budget_limit FLOAT,
    budget_unlimited BOOLEAN DEFAULT FALSE,
    allergies JSONB DEFAULT '[]',
    disliked_products JSONB DEFAULT '[]',
    local_cuisine_preference BOOLEAN DEFAULT TRUE,
    is_onboarding_completed BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    last_interaction TIMESTAMP,
    registration_source VARCHAR(20) DEFAULT 'whatsapp',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    onboarding_step VARCHAR(20)
);

-- Сообщения
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(36) PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    message_text TEXT,
    message_type VARCHAR(20) DEFAULT 'text',
    status VARCHAR(20) DEFAULT 'pending',
    error_type VARCHAR(50),
    attempts INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT NOW(),
    last_attempt TIMESTAMP,
    is_processed BOOLEAN DEFAULT FALSE,
    context JSONB
);

-- Планы диет
CREATE TABLE IF NOT EXISTS diet_plans (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    version VARCHAR(10) DEFAULT 'short',
    status VARCHAR(20) DEFAULT 'pending',
    daily_plans JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    budget_limit FLOAT,
    estimated_weekly_price FLOAT,
    general_recommendations TEXT,
    personalized_note TEXT,
    caloric_deficit TEXT,
    caloric_proficit TEXT,
    ai_generated BOOLEAN DEFAULT TRUE,
    dietitian_approved BOOLEAN DEFAULT FALSE,
    dietitian_comments TEXT,
    modifications_history JSONB DEFAULT '[]'
);

-- Продукты
CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(36) PRIMARY KEY,
    name TEXT NOT NULL,
    local_name TEXT,
    category VARCHAR(20),
    is_local BOOLEAN DEFAULT FALSE,
    typical_unit VARCHAR(10),
    nutrition JSONB,
    store_prices JSONB DEFAULT '{}',
    seasonal BOOLEAN DEFAULT FALSE,
    seasonal_months JSONB DEFAULT '[]',
    regions JSONB DEFAULT '[]',
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Списки покупок
CREATE TABLE IF NOT EXISTS shopping_lists (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    diet_plan_id VARCHAR(36) REFERENCES diet_plans(id),
    items JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    total_estimated_price FLOAT,
    delivery_integration VARCHAR(20),
    delivery_cart_id VARCHAR(36)
);

-- Записи веса
CREATE TABLE IF NOT EXISTS weight_entries (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    weight FLOAT NOT NULL,
    date DATE DEFAULT CURRENT_DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Записи потребления воды
CREATE TABLE IF NOT EXISTS water_entries (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    amount FLOAT NOT NULL,
    date DATE DEFAULT CURRENT_DATE,
    time TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Записи соблюдения плана питания
CREATE TABLE IF NOT EXISTS compliance (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    date DATE DEFAULT CURRENT_DATE,
    meal_type VARCHAR(20),
    status VARCHAR(20),
    notes TEXT,
    alternative_meal TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Сводная таблица соблюдения плана по дням
CREATE TABLE IF NOT EXISTS daily_compliance (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    date DATE DEFAULT CURRENT_DATE,
    meals JSONB DEFAULT '{}',
    overall_score FLOAT DEFAULT 0,
    notes TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Напоминания
CREATE TABLE IF NOT EXISTS reminders (
    id VARCHAR(36) PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    reminder_type VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone_number);
CREATE INDEX IF NOT EXISTS idx_diet_plans_user_id ON diet_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_diet_plans_status ON diet_plans(status);
CREATE INDEX IF NOT EXISTS idx_messages_phone ON messages(phone_number);
CREATE INDEX IF NOT EXISTS idx_reminders_phone_type ON reminders(phone_number, reminder_type);
CREATE INDEX IF NOT EXISTS idx_weight_entries_user_date ON weight_entries(user_id, date);
CREATE INDEX IF NOT EXISTS idx_water_entries_user_date ON water_entries(user_id, date);
CREATE INDEX IF NOT EXISTS idx_compliance_user_date ON compliance(user_id, date);