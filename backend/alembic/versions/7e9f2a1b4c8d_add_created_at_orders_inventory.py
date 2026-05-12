"""add created_at to orders and inventory_movements

Revision ID: 7e9f2a1b4c8d
Revises: 50c5877a72a5
Create Date: 2026-05-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7e9f2a1b4c8d"
down_revision: Union[str, Sequence[str], None] = "50c5877a72a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Mevcut satırlar için anında doldurulsun diye server_default kullanıyoruz.
    op.add_column(
        "orders",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.add_column(
        "inventory_movements",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def downgrade() -> None:
    op.drop_column("inventory_movements", "created_at")
    op.drop_column("orders", "created_at")
