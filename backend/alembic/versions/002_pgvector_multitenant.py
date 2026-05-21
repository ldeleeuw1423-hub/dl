"""pgvector similarity + multi-tenant organizations

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

Adds:
- pgvector extension
- organizations table
- organization_id FK columns on users, projects and historical_projects
- embedding vector(1536) column on historical_projects
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ------------------------------------------------------------------
    # organizations table
    # ------------------------------------------------------------------
    op.create_table(
        'organizations',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('uuid_generate_v4()'),
            nullable=False,
        ),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('subscription_tier', sa.String(50), nullable=False, server_default='free'),
        sa.Column('max_projects', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('max_users', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('settings', postgresql.JSONB(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('idx_organizations_slug', 'organizations', ['slug'])

    # ------------------------------------------------------------------
    # users — add organization_id FK
    # ------------------------------------------------------------------
    op.add_column(
        'users',
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('organizations.id', ondelete='SET NULL'),
            nullable=True,
        ),
    )
    op.create_index('idx_users_organization_id', 'users', ['organization_id'])

    # ------------------------------------------------------------------
    # projects — add organization_id FK
    # ------------------------------------------------------------------
    op.add_column(
        'projects',
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('organizations.id', ondelete='SET NULL'),
            nullable=True,
        ),
    )
    op.create_index('idx_projects_organization_id', 'projects', ['organization_id'])

    # ------------------------------------------------------------------
    # historical_projects — replace text embedding column with vector
    # ------------------------------------------------------------------
    # Drop old text embedding column if it exists (created in migration 001)
    op.execute(
        "ALTER TABLE historical_projects DROP COLUMN IF EXISTS embedding"
    )
    # Add proper pgvector column
    op.execute(
        "ALTER TABLE historical_projects ADD COLUMN embedding vector(1536)"
    )
    # Add organization_id FK
    op.add_column(
        'historical_projects',
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('organizations.id', ondelete='SET NULL'),
            nullable=True,
        ),
    )
    op.create_index('idx_historical_organization_id', 'historical_projects', ['organization_id'])

    # IVFFlat index for approximate nearest-neighbour search
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_historical_embedding
        ON historical_projects
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 10)
        WHERE embedding IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_historical_embedding")
    op.drop_index('idx_historical_organization_id', table_name='historical_projects')
    op.drop_column('historical_projects', 'organization_id')
    op.execute("ALTER TABLE historical_projects DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE historical_projects ADD COLUMN embedding TEXT")

    op.drop_index('idx_projects_organization_id', table_name='projects')
    op.drop_column('projects', 'organization_id')

    op.drop_index('idx_users_organization_id', table_name='users')
    op.drop_column('users', 'organization_id')

    op.drop_index('idx_organizations_slug', table_name='organizations')
    op.drop_table('organizations')
