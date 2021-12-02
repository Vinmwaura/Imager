"""empty message

Revision ID: 0d9719ce3d94
Revises: 3cc224a1af9c
Create Date: 2021-12-02 16:32:37.640051

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0d9719ce3d94'
down_revision = '3cc224a1af9c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'image_tags', ['tag_name'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'image_tags', type_='unique')
    # ### end Alembic commands ###
