"""Changes d active to email_confirmed and added active field

Revision ID: 4260207e0a89
Revises: 8054d60ec2d2
Create Date: 2021-11-22 15:05:31.162496

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4260207e0a89'
down_revision = '8054d60ec2d2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('email_confirmed', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'email_confirmed')
    # ### end Alembic commands ###
