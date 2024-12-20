"""empty message

Revision ID: 002
Revises: 001
Create Date: 2024-12-07 12:40:06.180427

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # ### commands auto generated by Alembic - please adjust! ###
    if 'ds_rating' not in tables:
        op.create_table('ds_rating',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('ds_meta_data_id', sa.Integer(), nullable=False),
            sa.Column('rating', sa.Float(), nullable=False),
            sa.Column('rated_date', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['ds_meta_data_id'], ['ds_meta_data.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    if 'deposition' not in tables:
        op.create_table('deposition',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('dep_metadata', sa.JSON(), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False, default="draft"),
            sa.Column('doi', sa.String(length=250), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    with op.batch_alter_table('ds_meta_data', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rating', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ds_meta_data', schema=None) as batch_op:
        batch_op.drop_column('rating')

    # op.create_table('deposition',
    # sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    # sa.Column('dep_metadata', mysql.LONGTEXT(charset='utf8mb4', collation='utf8mb4_bin'), nullable=False),
    # sa.Column('status', mysql.VARCHAR(length=50), nullable=False),
    # sa.Column('doi', mysql.VARCHAR(length=250), nullable=True),
    # sa.PrimaryKeyConstraint('id'),
    # mysql_collate='utf8mb4_general_ci',
    # mysql_default_charset='utf8mb4',
    # mysql_engine='InnoDB'
    # )
    # with op.batch_alter_table('deposition', schema=None) as batch_op:
    # batch_op.create_index('doi', ['doi'], unique=True)

    op.drop_table('ds_rating')
    op.drop_table('deposition')
    # ### end Alembic commands ###
