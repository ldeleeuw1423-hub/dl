"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='engineer'),
        sa.Column('organization', sa.String(255), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )

    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('project_number', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('client', sa.String(255), nullable=True),
        sa.Column('location', sa.String(500), nullable=True),
        sa.Column('phase', sa.String(50), nullable=False, server_default='VO'),
        sa.Column('discipline', sa.String(50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('scope_description', sa.Text(), nullable=True),
        sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='GEOMETRY', srid=28992), nullable=True),
        sa.Column('budget_estimated', sa.Numeric(14, 2), nullable=True),
        sa.Column('budget_actual', sa.Numeric(14, 2), nullable=True),
        sa.Column('hours_estimated', sa.Numeric(10, 2), nullable=True),
        sa.Column('hours_actual', sa.Numeric(10, 2), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_number'),
    )

    op.create_table(
        'risks',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('probability', sa.Integer(), nullable=False),
        sa.Column('impact', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('owner', sa.String(255), nullable=True),
        sa.Column('mitigation_measure', sa.Text(), nullable=True),
        sa.Column('deadline', sa.Date(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('residual_risk', sa.Integer(), nullable=True),
        sa.Column('auto_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('source', sa.String(50), nullable=False, server_default='manual'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'estimations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('discipline', sa.String(50), nullable=True),
        sa.Column('hours_engineering', sa.Numeric(10, 2), nullable=True),
        sa.Column('hours_pm', sa.Numeric(10, 2), nullable=True),
        sa.Column('hours_om', sa.Numeric(10, 2), nullable=True),
        sa.Column('hours_workprep', sa.Numeric(10, 2), nullable=True),
        sa.Column('hours_execution', sa.Numeric(10, 2), nullable=True),
        sa.Column('cost_materials', sa.Numeric(14, 2), nullable=True),
        sa.Column('cost_total', sa.Numeric(14, 2), nullable=True),
        sa.Column('bandwidth_low', sa.Numeric(14, 2), nullable=True),
        sa.Column('bandwidth_high', sa.Numeric(14, 2), nullable=True),
        sa.Column('confidence_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('methodology', sa.String(100), nullable=True),
        sa.Column('similar_projects', postgresql.JSONB(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'permits',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permit_type', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('authority', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='required'),
        sa.Column('submission_date', sa.Date(), nullable=True),
        sa.Column('expected_approval', sa.Date(), nullable=True),
        sa.Column('actual_approval', sa.Date(), nullable=True),
        sa.Column('risk_level', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('delay_probability', sa.Integer(), nullable=True),
        sa.Column('owner', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('auto_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'historical_projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('reference_number', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('discipline', sa.String(50), nullable=False),
        sa.Column('location_type', sa.String(50), nullable=False),
        sa.Column('trace_length_m', sa.Numeric(10, 2), nullable=True),
        sa.Column('num_crossings', sa.Integer(), nullable=True),
        sa.Column('num_permits', sa.Integer(), nullable=True),
        sa.Column('num_stakeholders', sa.Integer(), nullable=True),
        sa.Column('hours_engineering', sa.Numeric(10, 2), nullable=True),
        sa.Column('hours_pm', sa.Numeric(10, 2), nullable=True),
        sa.Column('hours_om', sa.Numeric(10, 2), nullable=True),
        sa.Column('hours_workprep', sa.Numeric(10, 2), nullable=True),
        sa.Column('cost_execution', sa.Numeric(14, 2), nullable=True),
        sa.Column('cost_total', sa.Numeric(14, 2), nullable=True),
        sa.Column('duration_days', sa.Integer(), nullable=True),
        sa.Column('num_revisions', sa.Integer(), nullable=True),
        sa.Column('risks_count', sa.Integer(), nullable=True),
        sa.Column('issues_count', sa.Integer(), nullable=True),
        sa.Column('embedding', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reference_number'),
    )

    op.create_index('idx_projects_status', 'projects', ['status'])
    op.create_index('idx_projects_discipline', 'projects', ['discipline'])
    op.create_index('idx_risks_project_id', 'risks', ['project_id'])
    op.create_index('idx_estimations_project_id', 'estimations', ['project_id'])
    op.create_index('idx_permits_project_id', 'permits', ['project_id'])


def downgrade() -> None:
    op.drop_table('historical_projects')
    op.drop_table('permits')
    op.drop_table('estimations')
    op.drop_table('risks')
    op.drop_table('projects')
    op.drop_table('users')
