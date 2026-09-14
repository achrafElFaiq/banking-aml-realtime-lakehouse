"""Load settlement Parquet files into bronze.raw_settlements in Postgres."""

from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os

def create_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=5432,
        dbname="aml_lakehouse",
        user="aml",
        password="aml_secret",
    )


def load_settlement_file(file_path: Path) -> None:
    """Load a single settlement Parquet file into bronze.raw_settlements."""
    df = pd.read_parquet(file_path)

    if df.empty:
        print(f"⚠️  Empty file: {file_path}")
        return

    conn = create_db_connection()
    try:
        cur = conn.cursor()

        cur.execute("CREATE SCHEMA IF NOT EXISTS bronze")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bronze.raw_settlements (
                transaction_id      VARCHAR(36),
                sender_iban         VARCHAR(34),
                beneficiary_iban    VARCHAR(34),
                amount              VARCHAR(20),
                currency            VARCHAR(3),
                payment_channel     VARCHAR(20),
                status              VARCHAR(10),
                blocked_reason      VARCHAR(255),
                executed_at         TIMESTAMP,
                loaded_at           TIMESTAMP DEFAULT NOW()
            )
        """)

        rows = [tuple(row) for row in df.values]
        execute_values(
            cur,
            """
            INSERT INTO bronze.raw_settlements
                (transaction_id, sender_iban, beneficiary_iban, amount,
                 currency, payment_channel, status, blocked_reason, executed_at)
            VALUES %s
            """,
            rows,
        )

        conn.commit()
        print(f"✅ Loaded {len(df)} rows from {file_path.name}")
    finally:
        conn.close()


def load_all_settlements(directory: str = "data/settlements") -> None:
    """Load all Parquet files from the settlements directory."""
    settlement_dir = Path(directory)
    if not settlement_dir.exists():
        print("⚠️  No settlements directory found")
        return

    files = sorted(settlement_dir.glob("*.parquet"))
    if not files:
        print("⚠️  No Parquet files found")
        return

    for f in files:
        load_settlement_file(f)


if __name__ == "__main__":
    load_all_settlements()