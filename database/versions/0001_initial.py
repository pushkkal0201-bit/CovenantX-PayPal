"""Initial versioned aggregate and audit tables."""
from alembic import op
import sqlalchemy as sa
revision='0001'
down_revision=None
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('milestones',sa.Column('id',sa.String(36),primary_key=True),sa.Column('version',sa.Integer,nullable=False),sa.Column('data',sa.Text,nullable=False))
    op.create_table('audit_events',sa.Column('id',sa.String(80),primary_key=True),sa.Column('milestone_id',sa.String(36),nullable=False),sa.Column('data',sa.Text,nullable=False))
    op.create_index('ix_audit_events_milestone_id','audit_events',['milestone_id'])
    op.create_table('webhook_events',sa.Column('id',sa.String(100),primary_key=True),sa.Column('received_at',sa.String(40),nullable=False))
def downgrade():
    op.drop_table('webhook_events');op.drop_index('ix_audit_events_milestone_id','audit_events');op.drop_table('audit_events');op.drop_table('milestones')
