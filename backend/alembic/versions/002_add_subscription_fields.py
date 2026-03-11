"""Add subscription fields to users

Revision ID: 002_subscription
Revises: 001_add_genfriend_v2_features
Create Date: 2025-01-20

"""
from alembic import op
import sqlalchemy as sa

revision = '002_subscription'
down_revision = '001_add_genfriend_v2_features'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('users', sa.Column('subscription_tier', sa.String(20), server_default='free'))
    op.add_column('users', sa.Column('subscription_status', sa.String(20), server_default='active'))
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('stripe_subscription_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('subscription_started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('subscription_ends_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('monthly_message_count', sa.Integer(), server_default='0'))
    op.add_column('users', sa.Column('message_count_reset_at', sa.DateTime(timezone=True), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'subscription_tier')
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'stripe_customer_id')
    op.drop_column('users', 'stripe_subscription_id')
    op.drop_column('users', 'subscription_started_at')
    op.drop_column('users', 'subscription_ends_at')
    op.drop_column('users', 'monthly_message_count')
    op.drop_column('users', 'message_count_reset_at')
