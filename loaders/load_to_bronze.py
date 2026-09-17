"""Load data from Postgres prod_source into Snowflake Bronze schema."""

import os

import pandas as pd
import psycopg2
import snowflake.connector
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas

load_dotenv()


def get_postgres_conn() -> psycopg2.extensions.connection:
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=5432,
        dbname="aml_lakehouse",
        user="aml",
        password="aml_secret",
    )


def get_snowflake_conn() -> snowflake.connector.SnowflakeConnection:
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT", "rmuinzc-nm01875"),
        user=os.getenv("SNOWFLAKE_USER", "achrafelfaiq"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse="AML_WH",
        database="AML_LAKEHOUSE",
        schema="BRONZE",
    )


def load_table(
    pg_conn: psycopg2.extensions.connection,
    sf_conn: snowflake.connector.SnowflakeConnection,
    source_table: str,
    target_table: str,
) -> None:
    df = pd.read_sql(f"SELECT * FROM prod_source.{source_table}", pg_conn)

    if df.empty:
        print(f"⚠️  No data in prod_source.{source_table}")
        return

    df["ingested_at"] = pd.Timestamp.now()

    # Snowflake expects uppercase column names
    df.columns = [col.upper() for col in df.columns]

    success, num_chunks, num_rows, _ = write_pandas(
        sf_conn,
        df,
        target_table.upper(),
        auto_create_table=True,
        overwrite=True,
    )

    print(
        f"✅ {num_rows} rows loaded: prod_source.{source_table}"
        f" -> BRONZE.{target_table.upper()}"
    )


def load_bronze() -> None:
    pg_conn = get_postgres_conn()
    sf_conn = get_snowflake_conn()

    try:
        load_table(pg_conn, sf_conn, "customers", "raw_customers")
        load_table(pg_conn, sf_conn, "transactions", "raw_transactions")
    finally:
        pg_conn.close()
        sf_conn.close()


if __name__ == "__main__":
    load_bronze()