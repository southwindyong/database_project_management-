"""Add is_public column to projects table

Revision ID: 1d3e8ee9943e
Revises: 6854c8d92404
Create Date: 2024-11-09 17:23:11.021085

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1d3e8ee9943e'
down_revision = '6854c8d92404'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_public', sa.Boolean(), nullable=False,server_default=sa.false()))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_column('is_public')

    # ### end Alembic commands ###
