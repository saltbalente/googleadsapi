-- Migración inicial para el sistema de optimización de keywords
-- Crear todas las tablas necesarias para el sistema de health scores

-- Tabla de cuentas MCC y sus hijas
CREATE TABLE IF NOT EXISTS mcc_accounts (
    customer_id VARCHAR(50) PRIMARY KEY,
    account_name VARCHAR(255) NOT NULL,
    currency_code VARCHAR(10) NOT NULL,
    time_zone VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_sync TIMESTAMP WITH TIME ZONE,
    
    -- Metadata para escalabilidad
    account_type VARCHAR(20) DEFAULT 'child', -- 'mcc', 'child'
    parent_customer_id VARCHAR(50),
    
    CONSTRAINT fk_parent_account FOREIGN KEY (parent_customer_id) 
        REFERENCES mcc_accounts(customer_id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_mcc_parent ON mcc_accounts(parent_customer_id);
CREATE INDEX IF NOT EXISTS idx_mcc_active ON mcc_accounts(is_active);

-- Tabla de históricos de métricas de keywords
CREATE TABLE IF NOT EXISTS keyword_metrics_history (
    id BIGSERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    campaign_id VARCHAR(50) NOT NULL,
    campaign_name VARCHAR(255) NOT NULL,
    ad_group_id VARCHAR(50) NOT NULL,
    ad_group_name VARCHAR(255) NOT NULL,
    keyword_text VARCHAR(500) NOT NULL,
    match_type VARCHAR(20),
    status VARCHAR(20),
    quality_score INTEGER,
    
    -- Métricas principales
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    cost_micros BIGINT DEFAULT 0,
    conversions DECIMAL(10, 2) DEFAULT 0,
    conversions_value DECIMAL(12, 2) DEFAULT 0,
    ctr DECIMAL(5, 4),
    average_cpc DECIMAL(10, 2),
    
    -- Metadata temporal
    date DATE NOT NULL,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints para integridad
    CONSTRAINT unique_keyword_date UNIQUE (customer_id, campaign_id, ad_group_id, keyword_text, date),
    CONSTRAINT fk_keyword_account FOREIGN KEY (customer_id) 
        REFERENCES mcc_accounts(customer_id) ON DELETE CASCADE
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_keyword_customer ON keyword_metrics_history(customer_id);
CREATE INDEX IF NOT EXISTS idx_keyword_date ON keyword_metrics_history(date DESC);
CREATE INDEX IF NOT EXISTS idx_keyword_campaign ON keyword_metrics_history(campaign_id);
CREATE INDEX IF NOT EXISTS idx_keyword_text ON keyword_metrics_history(keyword_text);
CREATE INDEX IF NOT EXISTS idx_keyword_composite ON keyword_metrics_history(customer_id, date DESC, cost_micros DESC);

-- Tabla de benchmarks personalizados por cuenta
CREATE TABLE IF NOT EXISTS keyword_benchmarks (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    target_conv_rate DECIMAL(5, 4) DEFAULT 0.02, -- 2%
    target_cpa DECIMAL(12, 2) DEFAULT 200000.00, -- COP
    benchmark_ctr DECIMAL(5, 4) DEFAULT 0.03, -- 3%
    min_quality_score INTEGER DEFAULT 5,
    
    -- Configuración avanzada
    industry_vertical VARCHAR(50),
    seasonality_factor DECIMAL(3, 2) DEFAULT 1.00,
    risk_tolerance VARCHAR(20) DEFAULT 'moderate', -- conservative, moderate, aggressive
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    
    CONSTRAINT unique_customer_benchmark UNIQUE (customer_id),
    CONSTRAINT fk_benchmark_account FOREIGN KEY (customer_id) 
        REFERENCES mcc_accounts(customer_id) ON DELETE CASCADE,
    CONSTRAINT check_conv_rate CHECK (target_conv_rate >= 0 AND target_conv_rate <= 1),
    CONSTRAINT check_ctr CHECK (benchmark_ctr >= 0 AND benchmark_ctr <= 1),
    CONSTRAINT check_quality_score CHECK (min_quality_score >= 1 AND min_quality_score <= 10)
);

CREATE INDEX IF NOT EXISTS idx_benchmark_customer ON keyword_benchmarks(customer_id);

-- Tabla de health scores calculados
CREATE TABLE IF NOT EXISTS keyword_health_scores (
    id BIGSERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    campaign_id VARCHAR(50) NOT NULL,
    ad_group_id VARCHAR(50) NOT NULL,
    keyword_text VARCHAR(500) NOT NULL,
    
    -- Componentes del health score
    health_score DECIMAL(5, 2) NOT NULL,
    conv_rate_score DECIMAL(5, 2) DEFAULT 0,
    cpa_score DECIMAL(5, 2) DEFAULT 0,
    ctr_score DECIMAL(5, 2) DEFAULT 0,
    confidence_score DECIMAL(5, 2) DEFAULT 0,
    quality_score_points DECIMAL(5, 2) DEFAULT 0,
    
    -- Clasificación y recomendación
    health_category VARCHAR(20) NOT NULL, -- 'excellent', 'good', 'warning', 'critical'
    recommended_action VARCHAR(50) NOT NULL, -- 'increase_bid', 'decrease_bid', 'pause', 'monitor'
    action_priority INTEGER DEFAULT 5, -- 1-10, donde 1 es máxima prioridad
    
    -- Contexto de cálculo
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_period_start DATE NOT NULL,
    data_period_end DATE NOT NULL,
    benchmark_version INTEGER DEFAULT 1,
    
    -- Métricas de contexto
    total_spend DECIMAL(12, 2),
    total_conversions DECIMAL(10, 2),
    total_clicks INTEGER,
    

    CONSTRAINT fk_health_account FOREIGN KEY (customer_id) 
        REFERENCES mcc_accounts(customer_id) ON DELETE CASCADE,
    CONSTRAINT check_health_score CHECK (health_score >= 0 AND health_score <= 100),
    CONSTRAINT check_priority CHECK (action_priority >= 1 AND action_priority <= 10)
);

-- Índices para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_health_score ON keyword_health_scores(health_score DESC);
CREATE INDEX IF NOT EXISTS idx_health_category ON keyword_health_scores(health_category);
CREATE INDEX IF NOT EXISTS idx_health_customer_date ON keyword_health_scores(customer_id, calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_health_action ON keyword_health_scores(recommended_action, action_priority);

-- Tabla de acciones de optimización ejecutadas
CREATE TABLE IF NOT EXISTS optimization_actions (
    id BIGSERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    execution_id VARCHAR(100) NOT NULL, -- UUID para agrupar acciones en lote
    
    -- Identificación del keyword
    campaign_id VARCHAR(50) NOT NULL,
    ad_group_id VARCHAR(50) NOT NULL,
    keyword_text VARCHAR(500) NOT NULL,
    
    -- Detalles de la acción
    action_type VARCHAR(50) NOT NULL, -- 'pause', 'increase_bid', 'decrease_bid', 'recreate'
    old_bid DECIMAL(12, 2),
    new_bid DECIMAL(12, 2),
    bid_change_percent DECIMAL(5, 2),
    
    -- Justificación y contexto
    justification TEXT,
    health_score_before DECIMAL(5, 2),
    risk_level VARCHAR(20), -- 'low', 'medium', 'high'
    
    -- Estado de ejecución
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'executed', 'failed', 'rolled_back'
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    executed_at TIMESTAMP WITH TIME ZONE,
    executed_by VARCHAR(100),
    
    -- Metadata de API
    google_ads_operation_id VARCHAR(100),
    api_response TEXT,
    error_message TEXT,
    
    CONSTRAINT fk_action_account FOREIGN KEY (customer_id) 
        REFERENCES mcc_accounts(customer_id) ON DELETE CASCADE,
    CONSTRAINT check_bid_change CHECK (ABS(bid_change_percent) <= 30) -- Guardrail de ±30%
);

-- Índices para auditoría y performance
CREATE INDEX IF NOT EXISTS idx_action_customer ON optimization_actions(customer_id);
CREATE INDEX IF NOT EXISTS idx_action_execution ON optimization_actions(execution_id);
CREATE INDEX IF NOT EXISTS idx_action_status ON optimization_actions(status);
CREATE INDEX IF NOT EXISTS idx_action_scheduled ON optimization_actions(scheduled_at DESC);

-- Tabla de resultados post-ejecución
CREATE TABLE IF NOT EXISTS action_results (
    id BIGSERIAL PRIMARY KEY,
    action_id BIGINT NOT NULL,
    
    -- Métricas de impacto
    success BOOLEAN NOT NULL,
    error_message TEXT,
    
    -- Impacto medido
    impact_spend DECIMAL(12, 2),
    impact_conversions DECIMAL(10, 2),
    impact_cpa DECIMAL(12, 2),
    impact_ctr DECIMAL(5, 4),
    
    -- Contexto temporal
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    days_after_execution INTEGER NOT NULL,
    measurement_period_start DATE,
    measurement_period_end DATE,
    
    -- Evaluación del resultado
    result_category VARCHAR(20), -- 'positive', 'neutral', 'negative'
    rollback_recommended BOOLEAN DEFAULT false,
    
    CONSTRAINT fk_result_action FOREIGN KEY (action_id) 
        REFERENCES optimization_actions(id) ON DELETE CASCADE,
    CONSTRAINT check_days_after CHECK (days_after_execution >= 0 AND days_after_execution <= 30)
);

CREATE INDEX IF NOT EXISTS idx_result_action ON action_results(action_id);
CREATE INDEX IF NOT EXISTS idx_result_measured ON action_results(measured_at DESC);
CREATE INDEX IF NOT EXISTS idx_result_category ON action_results(result_category);

-- Insertar cuentas por defecto primero
INSERT INTO mcc_accounts (customer_id, account_name, currency_code, time_zone, account_type)
VALUES 
('default', 'Default Template', 'COP', 'America/Bogota', 'template'),
('ecommerce_default', 'E-commerce Template', 'COP', 'America/Bogota', 'template'),
('lead_gen_default', 'Lead Generation Template', 'COP', 'America/Bogota', 'template'),
('saas_default', 'SaaS Template', 'COP', 'America/Bogota', 'template')
ON CONFLICT (customer_id) DO NOTHING;

-- Insertar benchmarks por defecto para nuevas cuentas
INSERT INTO keyword_benchmarks (customer_id, target_conv_rate, target_cpa, benchmark_ctr, min_quality_score, industry_vertical)
VALUES 
('default', 0.02, 200000.00, 0.03, 5, 'general'),
('ecommerce_default', 0.025, 150000.00, 0.035, 6, 'ecommerce'),
('lead_gen_default', 0.015, 300000.00, 0.025, 5, 'lead_generation'),
('saas_default', 0.03, 100000.00, 0.04, 7, 'saas')
ON CONFLICT (customer_id) DO NOTHING;

-- Crear función para auto-asignar benchmarks a nuevas cuentas
CREATE OR REPLACE FUNCTION assign_default_benchmarks()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO keyword_benchmarks (customer_id, target_conv_rate, target_cpa, benchmark_ctr, min_quality_score, industry_vertical)
    VALUES (NEW.customer_id, 0.02, 200000.00, 0.03, 5, 'general')
    ON CONFLICT (customer_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para auto-asignar benchmarks
DROP TRIGGER IF EXISTS trigger_assign_benchmarks ON mcc_accounts;
CREATE TRIGGER trigger_assign_benchmarks
    AFTER INSERT ON mcc_accounts
    FOR EACH ROW
    EXECUTE FUNCTION assign_default_benchmarks();

-- Habilitar RLS (Row Level Security) para todas las tablas
ALTER TABLE mcc_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE keyword_metrics_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE keyword_benchmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE keyword_health_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE optimization_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE action_results ENABLE ROW LEVEL SECURITY;

-- Políticas RLS básicas (permitir todo para roles autenticados)
CREATE POLICY "Allow all for authenticated users" ON mcc_accounts FOR ALL TO authenticated USING (true);
CREATE POLICY "Allow all for authenticated users" ON keyword_metrics_history FOR ALL TO authenticated USING (true);
CREATE POLICY "Allow all for authenticated users" ON keyword_benchmarks FOR ALL TO authenticated USING (true);
CREATE POLICY "Allow all for authenticated users" ON keyword_health_scores FOR ALL TO authenticated USING (true);
CREATE POLICY "Allow all for authenticated users" ON optimization_actions FOR ALL TO authenticated USING (true);
CREATE POLICY "Allow all for authenticated users" ON action_results FOR ALL TO authenticated USING (true);

-- Permisos para roles anon y authenticated
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;