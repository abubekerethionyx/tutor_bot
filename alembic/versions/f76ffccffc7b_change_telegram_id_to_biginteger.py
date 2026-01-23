"""change telegram_id to BigInteger

Revision ID: f76ffccffc7b
Revises: 
Create Date: 2026-01-24 00:11:20.582102

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f76ffccffc7b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy import BigInteger, Integer

def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('telegram_id', type_=BigInteger(), existing_type=Integer())


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('telegram_id', type_=Integer(), existing_type=BigInteger())
