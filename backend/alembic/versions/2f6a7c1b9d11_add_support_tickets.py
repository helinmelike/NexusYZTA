"""add support tickets

Revision ID: 2f6a7c1b9d11
Revises: 8bc4ac1605e1
Create Date: 2026-05-09 22:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f6a7c1b9d11"
down_revision: Union[str, Sequence[str], None] = "8bc4ac1605e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "support_tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_support_tickets_id"), "support_tickets", ["id"], unique=False)
    op.create_index(op.f("ix_support_tickets_customer_id"), "support_tickets", ["customer_id"], unique=False)
    op.create_index(op.f("ix_support_tickets_telegram_user_id"), "support_tickets", ["telegram_user_id"], unique=False)
    op.create_index(op.f("ix_support_tickets_status"), "support_tickets", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_support_tickets_status"), table_name="support_tickets")
    op.drop_index(op.f("ix_support_tickets_telegram_user_id"), table_name="support_tickets")
    op.drop_index(op.f("ix_support_tickets_customer_id"), table_name="support_tickets")
    op.drop_index(op.f("ix_support_tickets_id"), table_name="support_tickets")
    op.drop_table("support_tickets")
