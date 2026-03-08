"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Audit Logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(255)),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("request_data", postgresql.JSONB, nullable=False),
        sa.Column("response_data", postgresql.JSONB),
        sa.Column("pii_detected", postgresql.JSONB, server_default="'[]'"),
        sa.Column("response_pii_detected", postgresql.JSONB, server_default="'[]'"),
        sa.Column("tokens_input", sa.Integer),
        sa.Column("tokens_output", sa.Integer),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("cost_usd", sa.Numeric(10, 6)),
        sa.Column("compliance_framework", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("idx_audit_logs_time", "audit_logs", [sa.text("created_at DESC")])
    op.create_index("idx_audit_logs_user", "audit_logs", ["user_id", sa.text("created_at DESC")])

    # Immutability trigger for audit_logs
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Audit logs are immutable and cannot be modified or deleted';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER audit_logs_immutable
            BEFORE UPDATE OR DELETE ON audit_logs
            FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_modification();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_logs_immutable ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_modification()")
    op.drop_table("audit_logs")
