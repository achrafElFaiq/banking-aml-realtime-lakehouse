"""Load settlement Parquet files into Snowflake Bronze."""

import os
from pathlib import Path

import pandas as pd
import snowflake.connector
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas

load_dotenv()


def get_snowflake_conn() -> snowflake.connector.SnowflakeConnection:
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT", "rmuinzc-nm01875"),
        user=os.getenv("SNOWFLAKE_USER", "achrafelfaiq"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse="AML_WH",
        database="AML_LAKEHOUSE",
        schema="BRONZE",
    )


def load_settlement_file(file_path: Path) -> None:
    df = pd.read_parquet(file_path)

    if df.empty:
        print(f"⚠️  Empty file: {file_path}")
        return

    df["loaded_at"] = pd.Timestamp.now()
    df.columns = [col.upper() for col in df.columns]
    conn = get_snowflake_conn()
    try:
        success, num_chunks, num_rows, _ = write_pandas(
            conn,
            df,
            "RAW_SETTLEMENTS",
            auto_create_table=True,
            overwrite=True,
        )
        print(f"✅ {num_rows} rows loaded from {file_path.name}")
    finally:
        conn.close()


def load_all_settlements(directory: str = "data/settlements") -> None:
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