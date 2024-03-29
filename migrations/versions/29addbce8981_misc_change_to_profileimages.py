"""Misc change to profileImages

Revision ID: 29addbce8981
Revises: 652503f9224b
Create Date: 2021-11-29 16:32:17.304965

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '29addbce8981'
down_revision = '652503f9224b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('profile_images', sa.Column('file_id', sa.String(length=100), nullable=False))
    op.drop_column('profile_images', 'file_location')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('profile_images', sa.Column('file_location', sa.VARCHAR(length=100), autoincrement=False, nullable=False))
    op.drop_column('profile_images', 'file_id')
    # ### end Alembic commands ###
