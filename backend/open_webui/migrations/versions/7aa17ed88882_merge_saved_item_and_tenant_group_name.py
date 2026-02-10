"""merge_saved_item_and_tenant_group_name

Revision ID: 7aa17ed88882
Revises: 4f3d1b9e8a21, a1b2c3d4e5f6
Create Date: 2026-02-02 12:35:37.956344

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = '7aa17ed88882'
down_revision: Union[str, None] = ('4f3d1b9e8a21', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
