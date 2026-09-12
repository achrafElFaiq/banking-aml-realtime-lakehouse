"""Generate settlement files from pending transactions in the prod database.

Simulates a clearinghouse (Visa/Mastercard/STET) sending a daily file
confirming which transactions actually cleared. Reads PENDING transactions
from 1-3 days ago, marks them SETTLED, and writes a Parquet file.
"""

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import psycopg2


def create_db_connection() -> psycopg2.extensions.connection:
    """Connect to the mock prod database."""
    return psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="aml_lakehouse",
        user="aml",
        password="aml_secret",
    )


def fetch_pending_transactions(
    conn: psycopg2.extensions.connection,
    file_date: date,
) -> pd.DataFrame:
    """Fetch PENDING transactions from 1-3 days before file_date."""
    cutoff_recent = file_date - timedelta(days=1)
    cutoff_old = file_date - timedelta(days=3)

    query = """
        SELECT transaction_id, sender_iban, beneficiary_iban, amount,
               currency, payment_channel, status, blocked_reason, executed_at
        FROM prod_source.transactions
        WHERE status = 'PENDING'
          AND executed_at::date BETWEEN %s AND %s
    """
    return pd.read_sql(query, conn, params=(cutoff_old, cutoff_recent))


def apply_settlement_corrections(df: pd.DataFrame) -> pd.DataFrame:
    """Simulate clearing corrections — small amount adjustments on ~5% of rows."""
    df = df.copy()
    df["status"] = "SETTLED"

    # 5% of transactions get a small amount correction (FX, fees, tips)
    mask = df.sample(frac=0.05, random_state=42).index if len(df) > 20 else []
    for idx in mask:
        original = df.at[idx, "amount"]
        # Parse European format, add small correction, convert back
        amount = float(original.replace(",", "."))
        correction = round(random.uniform(0.50, 5.00), 2)
        corrected = round(amount + correction, 2)
        df.at[idx, "amount"] = f"{corrected:.2f}".replace(".", ",")

    return df


def generate_settlement_file(file_date: date, output_dir: str = "data/settlements") -> Path:
    """Generate a daily settlement Parquet file."""
    conn = create_db_connection()

    try:
        df = fetch_pending_transactions(conn, file_date)

        if df.empty:
            print(f"⚠️  No pending transactions found for settlement on {file_date}")
            return Path(output_dir) / f"settlement_{file_date}.parquet"

        df = apply_settlement_corrections(df)

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        file_path = output_path / f"settlement_{file_date}.parquet"
        df.to_parquet(file_path, index=False)

        print(f"✅ Settlement file: {file_path}")
        print(f"   {len(df)} transactions marked SETTLED")
        print(f"   Date range: {file_date - timedelta(days=3)} to {file_date - timedelta(days=1)}")

        return file_path
    finally:
        conn.close()


if __name__ == "__main__":
    # Generate settlement for today (confirms transactions from 1-3 days ago)
    today = date.today()
    generate_settlement_file(today)