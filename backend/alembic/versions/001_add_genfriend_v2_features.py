"""Add Gen-Friend V2 features: WOOP, Locke-Latham, If-Then Plans, Coach Personalization

Revision ID: 001_genfriend_v2
Revises:
Create Date: 2026-01-17

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = '001_genfriend_v2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def add_column_if_not_exists(table_name: str, column: sa.Column):
    if not column_exists(table_name, column.name):
        op.add_column(table_name, column)


def upgrade() -> None:
    # Add coach personalization columns to users table
    add_column_if_not_exists('users', sa.Column('preferred_name', sa.String(100), nullable=True))
    add_column_if_not_exists('users', sa.Column('coach_name', sa.String(100), server_default='Gen', nullable=True))
    add_column_if_not_exists('users', sa.Column('coach_relationship', sa.String(255), nullable=True))
    add_column_if_not_exists('users', sa.Column('coach_tone', sa.String(20), server_default='warm', nullable=True))
    add_column_if_not_exists('users', sa.Column('quiet_hours_start', sa.Time(), nullable=True))
    add_column_if_not_exists('users', sa.Column('quiet_hours_end', sa.Time(), nullable=True))
    add_column_if_not_exists('users', sa.Column('reflection_day', sa.String(10), server_default='sunday', nullable=True))
    add_column_if_not_exists('users', sa.Column('notification_level', sa.String(20), server_default='balanced', nullable=True))
    add_column_if_not_exists('users', sa.Column('voice_enabled', sa.Boolean(), server_default='false', nullable=True))
    add_column_if_not_exists('users', sa.Column('onboarding_step', sa.String(50), nullable=True))

    # Add Future You fields to goals table
    add_column_if_not_exists('goals', sa.Column('future_you_time_horizon', sa.String(20), nullable=True))
    add_column_if_not_exists('goals', sa.Column('future_you_visualization', sa.Text(), nullable=True))
    add_column_if_not_exists('goals', sa.Column('future_you_identity_statement', sa.Text(), nullable=True))

    # Add WOOP Framework fields to goals table
    add_column_if_not_exists('goals', sa.Column('woop_wish', sa.Text(), nullable=True))
    add_column_if_not_exists('goals', sa.Column('woop_outcome', sa.Text(), nullable=True))
    add_column_if_not_exists('goals', sa.Column('woop_primary_obstacle', sa.String(50), nullable=True))
    add_column_if_not_exists('goals', sa.Column('woop_custom_obstacle', sa.Text(), nullable=True))

    # Add Locke-Latham validation scores to goals table
    add_column_if_not_exists('goals', sa.Column('ll_clarity_score', sa.Integer(), nullable=True))
    add_column_if_not_exists('goals', sa.Column('ll_challenge_score', sa.Integer(), nullable=True))
    add_column_if_not_exists('goals', sa.Column('ll_commitment_score', sa.Integer(), nullable=True))
    add_column_if_not_exists('goals', sa.Column('ll_feedback_score', sa.Integer(), nullable=True))
    add_column_if_not_exists('goals', sa.Column('ll_complexity_score', sa.Integer(), nullable=True))

    # Add goal_type column (was missing from original schema)
    add_column_if_not_exists('goals', sa.Column('goal_type', sa.String(20), server_default='performance', nullable=True))

    # Add execution system and streak tracking to goals table
    add_column_if_not_exists('goals', sa.Column('execution_system', sa.JSON(), nullable=True))
    add_column_if_not_exists('goals', sa.Column('current_streak', sa.Integer(), server_default='0', nullable=True))
    add_column_if_not_exists('goals', sa.Column('longest_streak', sa.Integer(), server_default='0', nullable=True))
    add_column_if_not_exists('goals', sa.Column('total_tasks_completed', sa.Integer(), server_default='0', nullable=True))
    add_column_if_not_exists('goals', sa.Column('total_tasks_created', sa.Integer(), server_default='0', nullable=True))

    # Add completion tracking to goals table
    add_column_if_not_exists('goals', sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))
    add_column_if_not_exists('goals', sa.Column('completion_reflection', sa.Text(), nullable=True))

    # Create if_then_plans table if not exists
    if not table_exists('if_then_plans'):
        op.create_table(
            'if_then_plans',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('goal_id', sa.String(36), sa.ForeignKey('goals.id', ondelete='CASCADE'), nullable=False),
            sa.Column('when_trigger', sa.Text(), nullable=False),
            sa.Column('then_action', sa.Text(), nullable=False),
            sa.Column('obstacle_type', sa.String(50), nullable=True),
            sa.Column('is_primary', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('times_triggered', sa.Integer(), server_default='0', nullable=False),
            sa.Column('times_used', sa.Integer(), server_default='0', nullable=False),
            sa.Column('times_effective', sa.Integer(), server_default='0', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('ix_if_then_plans_goal_id', 'if_then_plans', ['goal_id'])

    # Create if_then_logs table if not exists
    if not table_exists('if_then_logs'):
        op.create_table(
            'if_then_logs',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('if_then_plan_id', sa.String(36), sa.ForeignKey('if_then_plans.id', ondelete='CASCADE'), nullable=False),
            sa.Column('task_id', sa.String(36), nullable=True),
            sa.Column('was_triggered', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('was_used', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('was_effective', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('context', sa.Text(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('ix_if_then_logs_plan_id', 'if_then_logs', ['if_then_plan_id'])


def downgrade() -> None:
    # Drop if_then_logs table
    if table_exists('if_then_logs'):
        op.drop_index('ix_if_then_logs_plan_id', 'if_then_logs')
        op.drop_table('if_then_logs')

    # Drop if_then_plans table
    if table_exists('if_then_plans'):
        op.drop_index('ix_if_then_plans_goal_id', 'if_then_plans')
        op.drop_table('if_then_plans')

    # Remove completion tracking columns from goals
    if column_exists('goals', 'completion_reflection'):
        op.drop_column('goals', 'completion_reflection')
    if column_exists('goals', 'completed_at'):
        op.drop_column('goals', 'completed_at')

    # Remove streak tracking columns from goals
    if column_exists('goals', 'total_tasks_created'):
        op.drop_column('goals', 'total_tasks_created')
    if column_exists('goals', 'total_tasks_completed'):
        op.drop_column('goals', 'total_tasks_completed')
    if column_exists('goals', 'longest_streak'):
        op.drop_column('goals', 'longest_streak')
    if column_exists('goals', 'current_streak'):
        op.drop_column('goals', 'current_streak')
    if column_exists('goals', 'execution_system'):
        op.drop_column('goals', 'execution_system')

    # Remove goal_type column
    if column_exists('goals', 'goal_type'):
        op.drop_column('goals', 'goal_type')

    # Remove Locke-Latham columns from goals
    if column_exists('goals', 'll_complexity_score'):
        op.drop_column('goals', 'll_complexity_score')
    if column_exists('goals', 'll_feedback_score'):
        op.drop_column('goals', 'll_feedback_score')
    if column_exists('goals', 'll_commitment_score'):
        op.drop_column('goals', 'll_commitment_score')
    if column_exists('goals', 'll_challenge_score'):
        op.drop_column('goals', 'll_challenge_score')
    if column_exists('goals', 'll_clarity_score'):
        op.drop_column('goals', 'll_clarity_score')

    # Remove WOOP columns from goals
    if column_exists('goals', 'woop_custom_obstacle'):
        op.drop_column('goals', 'woop_custom_obstacle')
    if column_exists('goals', 'woop_primary_obstacle'):
        op.drop_column('goals', 'woop_primary_obstacle')
    if column_exists('goals', 'woop_outcome'):
        op.drop_column('goals', 'woop_outcome')
    if column_exists('goals', 'woop_wish'):
        op.drop_column('goals', 'woop_wish')

    # Remove Future You columns from goals
    if column_exists('goals', 'future_you_identity_statement'):
        op.drop_column('goals', 'future_you_identity_statement')
    if column_exists('goals', 'future_you_visualization'):
        op.drop_column('goals', 'future_you_visualization')
    if column_exists('goals', 'future_you_time_horizon'):
        op.drop_column('goals', 'future_you_time_horizon')

    # Remove coach personalization columns from users
    if column_exists('users', 'onboarding_step'):
        op.drop_column('users', 'onboarding_step')
    if column_exists('users', 'voice_enabled'):
        op.drop_column('users', 'voice_enabled')
    if column_exists('users', 'notification_level'):
        op.drop_column('users', 'notification_level')
    if column_exists('users', 'reflection_day'):
        op.drop_column('users', 'reflection_day')
    if column_exists('users', 'quiet_hours_end'):
        op.drop_column('users', 'quiet_hours_end')
    if column_exists('users', 'quiet_hours_start'):
        op.drop_column('users', 'quiet_hours_start')
    if column_exists('users', 'coach_tone'):
        op.drop_column('users', 'coach_tone')
    if column_exists('users', 'coach_relationship'):
        op.drop_column('users', 'coach_relationship')
    if column_exists('users', 'coach_name'):
        op.drop_column('users', 'coach_name')
    if column_exists('users', 'preferred_name'):
        op.drop_column('users', 'preferred_name')
