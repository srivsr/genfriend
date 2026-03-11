"""Add strategic brain tables

Revision ID: 003_strategic_brain
Revises: 002_subscription
Create Date: 2026-02-26

"""
from alembic import op
import sqlalchemy as sa

revision = '003_strategic_brain'
down_revision = '002_subscription'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'opportunity_scores',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column('goal_id', sa.String(36), sa.ForeignKey('goals.id'), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('revenue_potential', sa.Integer(), server_default='0'),
        sa.Column('strategic_fit', sa.Integer(), server_default='0'),
        sa.Column('effort_complexity', sa.Integer(), server_default='0'),
        sa.Column('skill_match', sa.Integer(), server_default='0'),
        sa.Column('time_to_first_win', sa.Integer(), server_default='0'),
        sa.Column('risk_regret_cost', sa.Integer(), server_default='0'),
        sa.Column('total_score', sa.Float(), server_default='0.0'),
        sa.Column('reasoning', sa.JSON()),
        sa.Column('anti_goal_conflicts', sa.JSON()),
        sa.Column('status', sa.String(20), server_default='evaluated'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )

    op.create_table(
        'decision_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column('goal_id', sa.String(36), sa.ForeignKey('goals.id'), nullable=True),
        sa.Column('decision', sa.Text(), nullable=False),
        sa.Column('why', sa.Text()),
        sa.Column('expected_outcome', sa.Text()),
        sa.Column('review_date', sa.Date()),
        sa.Column('actual_outcome', sa.Text()),
        sa.Column('tags', sa.JSON()),
        sa.Column('status', sa.String(20), server_default='pending_review'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )

    op.create_table(
        'experiments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column('hypothesis', sa.Text(), nullable=False),
        sa.Column('action', sa.Text()),
        sa.Column('result', sa.Text()),
        sa.Column('learning', sa.Text()),
        sa.Column('tags', sa.JSON()),
        sa.Column('status', sa.String(20), server_default='open'),
        sa.Column('closed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )

    op.create_table(
        'distraction_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('condition', sa.Text(), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('rule_type', sa.String(20), server_default='custom'),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )

    op.add_column('identities', sa.Column('anti_goals', sa.JSON(), nullable=True))
    op.add_column('identities', sa.Column('weekly_hours_available', sa.Integer(), nullable=True))
    op.add_column('identities', sa.Column('monthly_budget', sa.Float(), nullable=True))
    op.add_column('identities', sa.Column('health_limits', sa.Text(), nullable=True))
    op.add_column('identities', sa.Column('risk_tolerance', sa.String(10), nullable=True))

def downgrade() -> None:
    op.drop_table('distraction_rules')
    op.drop_table('experiments')
    op.drop_table('decision_logs')
    op.drop_table('opportunity_scores')
    op.drop_column('identities', 'anti_goals')
    op.drop_column('identities', 'weekly_hours_available')
    op.drop_column('identities', 'monthly_budget')
    op.drop_column('identities', 'health_limits')
    op.drop_column('identities', 'risk_tolerance')
