"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-03-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'partners',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('device_type', sa.String(50), nullable=False),
        sa.Column('brand_color', sa.String(7), server_default='#3D6B2C'),
        sa.Column('logo_url', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        'customers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('partner_id', UUID(as_uuid=True), sa.ForeignKey('partners.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('tariff_type', sa.String(50), nullable=False, server_default='dynamic'),
        sa.Column('device_type', sa.String(50), nullable=False),
        sa.Column('monthly_kwh', sa.Numeric(10, 2), nullable=True),
        sa.Column('annual_saving_eur', sa.Numeric(10, 2), nullable=True),
        sa.Column('salary_day', sa.Integer, nullable=True),
        sa.Column('contract_start', sa.Date, nullable=False),
        sa.Column('contract_status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        'payments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount_eur', sa.Numeric(10, 2), nullable=False),
        sa.Column('period_month', sa.Date, nullable=False),
        sa.Column('due_date', sa.Date, nullable=False),
        sa.Column('paid_at', sa.DateTime, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('failure_reason', sa.String(100), nullable=True),
        sa.Column('failure_classified_by', sa.String(20), server_default='manual'),
        sa.Column('retry_count', sa.Integer, server_default='0'),
        sa.Column('max_retries', sa.Integer, server_default='3'),
        sa.Column('next_retry_date', sa.Date, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        'dunning_actions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('payment_id', UUID(as_uuid=True), sa.ForeignKey('payments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('ai_generated_message', sa.Text, nullable=True),
        sa.Column('ai_failure_reason', sa.String(100), nullable=True),
        sa.Column('ai_confidence', sa.Numeric(4, 3), nullable=True),
        sa.Column('retry_scheduled_for', sa.Date, nullable=True),
        sa.Column('triggered_by', sa.String(50), server_default='system'),
        sa.Column('outcome', sa.String(50), nullable=True),
        sa.Column('executed_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        'churn_scores',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('score', sa.Integer, nullable=False),
        sa.Column('risk_level', sa.String(20), nullable=False),
        sa.Column('reasoning', sa.Text, nullable=True),
        sa.Column('factors', JSONB, nullable=True),
        sa.Column('action_suggested', sa.Text, nullable=True),
        sa.Column('scored_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_customers_partner', 'customers', ['partner_id'])
    op.create_index('idx_customers_status', 'customers', ['contract_status'])
    op.create_index('idx_payments_customer', 'payments', ['customer_id'])
    op.create_index('idx_payments_status', 'payments', ['status'])
    op.create_index('idx_dunning_customer', 'dunning_actions', ['customer_id'])
    op.create_index('idx_dunning_payment', 'dunning_actions', ['payment_id'])
    op.create_index('idx_churn_customer', 'churn_scores', ['customer_id'])
    op.create_index('idx_churn_scored_at', 'churn_scores', ['scored_at'])


def downgrade() -> None:
    op.drop_table('churn_scores')
    op.drop_table('dunning_actions')
    op.drop_table('payments')
    op.drop_table('customers')
    op.drop_table('partners')
