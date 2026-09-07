"""enable postgis extension

Revision ID: e67ac2ef95c1
Revises: 
Create Date: 2026-09-04 07:34:18.796039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e67ac2ef95c1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")


def downgrade() -> None:
    # Deliberately not dropping the extension on downgrade — other schemas
    # or tables outside NETRIXA's ownership might depend on it.
    pass
