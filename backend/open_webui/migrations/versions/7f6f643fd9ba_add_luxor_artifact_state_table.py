"""Add luxor_artifact_state table

Revision ID: 7f6f643fd9ba
Revises: b3a7c2d9e4f1
Create Date: 2026-01-20 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from open_webui.internal.db import get_table_name

# revision identifiers, used by Alembic.
revision: str = "7f6f643fd9ba"
down_revision: Union[str, None] = "b3a7c2d9e4f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        get_table_name("luxor_artifact_state"),
        sa.Column("s3_key", sa.String(length=255), nullable=False),
        sa.Column("artifact_uuid", sa.String(length=255), nullable=True),
        sa.Column("ensemble_key", sa.String(length=255), nullable=True),
        sa.Column("faiss_key", sa.String(length=255), nullable=True),
        sa.Column("kg_key", sa.String(length=255), nullable=True),
        sa.Column(
            "build_lock",
            sa.Boolean(),
            nullable=False,
            server_default=sa.sql.expression.false(),
        ),
        sa.Column(
            "build_scheduled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.sql.expression.false(),
        ),
        sa.Column(
            "last_built",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("tenant_id", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("s3_key"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            [f"{get_table_name('tenant')}.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            [f"{get_table_name('user')}.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "idx_luxor_artifact_state_tenant_id",
        get_table_name("luxor_artifact_state"),
        ["tenant_id"],
    )
    op.create_index(
        "idx_luxor_artifact_state_user_id",
        get_table_name("luxor_artifact_state"),
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_luxor_artifact_state_user_id",
        table_name=get_table_name("luxor_artifact_state"),
    )
    op.drop_index(
        "idx_luxor_artifact_state_tenant_id",
        table_name=get_table_name("luxor_artifact_state"),
    )
    op.drop_table(get_table_name("luxor_artifact_state"))
