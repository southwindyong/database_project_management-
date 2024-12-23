"""2

Revision ID: 6854c8d92404
Revises: 
Create Date: 2024-11-07 20:50:37.292093

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6854c8d92404'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('projects',
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('project_name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('priority', sa.String(length=50), nullable=False),
    sa.Column('budget', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('project_id')
    )
    op.create_table('users',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=False),
    sa.Column('password_hash', sa.String(length=200), nullable=False),
    sa.Column('first_name', sa.String(length=50), nullable=False),
    sa.Column('last_name', sa.String(length=50), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('user_id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('approvals',
    sa.Column('approval_id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('approval_type', sa.String(length=50), nullable=False),
    sa.Column('requested_by', sa.Integer(), nullable=False),
    sa.Column('approved_by', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('approval_date', sa.DateTime(), nullable=True),
    sa.Column('comments', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['approved_by'], ['users.user_id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ),
    sa.ForeignKeyConstraint(['requested_by'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('approval_id')
    )
    op.create_table('project_documents',
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('document_name', sa.String(length=100), nullable=False),
    sa.Column('document_description', sa.String(length=255), nullable=True),
    sa.Column('document_type', sa.String(length=50), nullable=False),
    sa.Column('document_link', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('uploaded_by', sa.Integer(), nullable=False),
    sa.Column('access_level', sa.String(length=50), nullable=False),
    sa.Column('tags', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ),
    sa.ForeignKeyConstraint(['uploaded_by'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('document_id')
    )
    op.create_table('project_members',
    sa.Column('member_id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.Column('join_date', sa.DateTime(), nullable=False),
    sa.Column('leave_date', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('member_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('project_members')
    op.drop_table('project_documents')
    op.drop_table('approvals')
    op.drop_table('users')
    op.drop_table('projects')
    # ### end Alembic commands ###
