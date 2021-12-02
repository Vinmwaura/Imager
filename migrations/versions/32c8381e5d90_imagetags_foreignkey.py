"""ImageTags foreignkey

Revision ID: 32c8381e5d90
Revises: 0d9719ce3d94
Create Date: 2021-12-02 16:37:56.361264

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '32c8381e5d90'
down_revision = '0d9719ce3d94'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('image_content', 'tag_5')
    op.drop_column('image_content', 'tag_3')
    op.drop_column('image_content', 'tag_1')
    op.drop_column('image_content', 'tag_8')
    op.drop_column('image_content', 'tag_7')
    op.drop_column('image_content', 'tag_2')
    op.drop_column('image_content', 'tag_6')
    op.drop_column('image_content', 'tag_4')
    op.add_column('image_tags', sa.Column('image_content_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'image_tags', 'image_content', ['image_content_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'image_tags', type_='foreignkey')
    op.drop_column('image_tags', 'image_content_id')
    op.add_column('image_content', sa.Column('tag_4', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    op.add_column('image_content', sa.Column('tag_6', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    op.add_column('image_content', sa.Column('tag_2', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    op.add_column('image_content', sa.Column('tag_7', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    op.add_column('image_content', sa.Column('tag_8', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    op.add_column('image_content', sa.Column('tag_1', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    op.add_column('image_content', sa.Column('tag_3', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    op.add_column('image_content', sa.Column('tag_5', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
