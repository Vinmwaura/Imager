"""Added image models

Revision ID: 78c89b6695f5
Revises: 3ec1c99156f1
Create Date: 2021-11-27 03:18:25.928092

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '78c89b6695f5'
down_revision = '3ec1c99156f1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_content',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('content_location', sa.String(length=100), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('image_content',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_content_id', sa.Integer(), nullable=True),
    sa.Column('file_location', sa.String(length=100), nullable=False),
    sa.Column('image_name', sa.String(length=20), nullable=False),
    sa.Column('image_desc', sa.String(length=100), nullable=True),
    sa.Column('upload_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_content_id'], ['user_content.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('profile_images',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_content_id', sa.Integer(), nullable=True),
    sa.Column('file_location', sa.String(length=100), nullable=False),
    sa.ForeignKeyConstraint(['user_content_id'], ['user_content.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('image_tags',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('image_id', sa.Integer(), nullable=True),
    sa.Column('tag_1', sa.String(length=20), nullable=True),
    sa.Column('tag_2', sa.String(length=20), nullable=True),
    sa.Column('tag_3', sa.String(length=20), nullable=True),
    sa.Column('tag_4', sa.String(length=20), nullable=True),
    sa.Column('tag_5', sa.String(length=20), nullable=True),
    sa.Column('tag_6', sa.String(length=20), nullable=True),
    sa.Column('tag_7', sa.String(length=20), nullable=True),
    sa.Column('tag_8', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['image_id'], ['image_content.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('image_tags')
    op.drop_table('profile_images')
    op.drop_table('image_content')
    op.drop_table('user_content')
    # ### end Alembic commands ###
