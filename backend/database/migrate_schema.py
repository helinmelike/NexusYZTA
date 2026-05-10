"""Schema migration helper for existing cooperative.db.

Run from the backend directory:
    python database/migrate_schema.py

This script adds missing Customer columns and creates the support_tickets table
without deleting existing data.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection

from database.db import engine


def table_exists(conn: Connection, table_name: str) -> bool:
    result = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table_name},
    )
    return result.first() is not None


def column_exists(conn: Connection, table_name: str, column_name: str) -> bool:
    result = conn.execute(text(f"PRAGMA table_info({table_name})"))
    return any(row[1] == column_name for row in result)


def add_column(conn: Connection, table_name: str, column_sql: str) -> None:
    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}"))


def create_support_tickets_table(conn: Connection) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                telegram_user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                status VARCHAR NOT NULL DEFAULT 'open',
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            )
            """
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_support_tickets_customer_id ON support_tickets(customer_id)"
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_support_tickets_telegram_user_id ON support_tickets(telegram_user_id)"
        )
    )
    conn.execute(
        text("CREATE INDEX IF NOT EXISTS ix_support_tickets_status ON support_tickets(status)")
    )


def migrate() -> None:
    with engine.begin() as conn:
        if not table_exists(conn, "customers"):
            raise RuntimeError("customers tablosu bulunamadı. Lütfen önce mevcut DB yapısını kontrol edin.")

        if not column_exists(conn, "customers", "telegram_user_id"):
            print("Ekleniyor: customers.telegram_user_id")
            add_column(conn, "customers", "telegram_user_id INTEGER")
        else:
            print("Zaten var: customers.telegram_user_id")

        if not column_exists(conn, "customers", "role"):
            print("Ekleniyor: customers.role")
            add_column(
                conn,
                "customers",
                "role VARCHAR NOT NULL DEFAULT 'customer'",
            )
            conn.execute(text("UPDATE customers SET role = 'customer' WHERE role IS NULL"))
        else:
            print("Zaten var: customers.role")

        if not table_exists(conn, "support_tickets"):
            print("Ekleniyor: support_tickets tablosu")
            create_support_tickets_table(conn)
        else:
            print("Zaten var: support_tickets tablosu")

    print("Migration tamamlandı.")


if __name__ == "__main__":
    migrate()
