-- Add response PII detection column to audit_logs
-- This tracks PII detected in LLM responses separately from input PII

ALTER TABLE audit_logs
ADD COLUMN response_pii_detected JSONB DEFAULT '[]';

COMMENT ON COLUMN audit_logs.response_pii_detected IS 'PII entities detected in LLM response content';
