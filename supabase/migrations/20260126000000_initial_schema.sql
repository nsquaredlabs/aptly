-- Aptly Initial Schema
-- This migration creates the core tables for the Aptly compliance middleware

-- Customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    plan VARCHAR(50) DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'enterprise')),
    compliance_frameworks TEXT[] DEFAULT '{}',
    retention_days INTEGER DEFAULT 2555,
    pii_redaction_mode VARCHAR(20) DEFAULT 'mask' CHECK (pii_redaction_mode IN ('mask', 'hash', 'remove')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- API Keys table (simplified - no scopes)
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    key_hash VARCHAR(64) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    rate_limit_per_hour INTEGER DEFAULT 1000,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash) WHERE NOT is_revoked;
CREATE INDEX idx_api_keys_customer ON api_keys(customer_id);

-- Audit Logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    user_id VARCHAR(255),

    -- Request metadata
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,

    -- Redacted content (NEVER store original PII)
    request_data JSONB NOT NULL,
    response_data JSONB,

    -- PII detection results
    pii_detected JSONB DEFAULT '[]',

    -- Metrics
    tokens_input INTEGER,
    tokens_output INTEGER,
    latency_ms INTEGER,
    cost_usd DECIMAL(10, 6),

    -- Compliance
    compliance_framework VARCHAR(20),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_customer_time ON audit_logs(customer_id, created_at DESC);
CREATE INDEX idx_audit_logs_user ON audit_logs(customer_id, user_id, created_at DESC);

-- Immutability: audit logs cannot be updated or deleted
CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are immutable and cannot be modified or deleted';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_logs_immutable
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_modification();

-- Enable RLS
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies (for direct Supabase dashboard access)
-- Backend uses service role key which bypasses RLS
CREATE POLICY "customers_own_data" ON customers
    FOR ALL USING (id = auth.uid());

CREATE POLICY "api_keys_own_data" ON api_keys
    FOR ALL USING (customer_id = auth.uid());

CREATE POLICY "audit_logs_own_data" ON audit_logs
    FOR SELECT USING (customer_id = auth.uid());

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
