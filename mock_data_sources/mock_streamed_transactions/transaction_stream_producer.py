"""Producer: simulates a payment gateway that writes to the prod DB and emits to Redpanda."""

import json
import time

import psycopg2
from kafka import KafkaProducer

from mock_data_sources.mock_prod_db.generate_fake_customers import Customer
from mock_data_sources.mock_streamed_transactions.generate_fake_transaction import (
    generate_transaction,
)


def create_kafka_producer() -> KafkaProducer:
    """Create a Kafka producer connected to Redpanda."""
    return KafkaProducer(
        bootstrap_servers=["localhost:9092"],
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
    )


def create_db_connection() -> psycopg2.extensions.connection:
    """Connect to the mock prod database."""
    return psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="aml_lakehouse",
        user="aml",
        password="aml_secret",
    )


def load_customers_from_db(conn: psycopg2.extensions.connection) -> list[Customer]:
    """Load existing customers from the prod database."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT customer_id, first_name, last_name, email, phone_number,
               iban, address, city, country, risk_tier, created_at
        FROM prod_source.customers
        """
    )
    rows = cur.fetchall()
    columns = [
        "customer_id", "first_name", "last_name", "email", "phone_number",
        "iban", "address", "city", "country", "risk_tier", "created_at",
    ]
    return [Customer(**dict(zip(columns, row))) for row in rows]


def write_to_db(conn: psycopg2.extensions.connection, txn: dict) -> None:
    """Write a transaction to prod_source.transactions."""
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO prod_source.transactions
            (transaction_id, sender_iban, beneficiary_iban, amount,
             currency, payment_channel, status, blocked_reason, executed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (transaction_id) DO NOTHING
        """,
        (
            txn["transaction_id"],
            txn["sender_iban"],
            txn["beneficiary_iban"],
            txn["amount"],
            txn["currency"],
            txn["payment_channel"],
            txn["status"],
            txn["blocked_reason"],
            txn["executed_at"],
        ),
    )
    conn.commit()


if __name__ == "__main__":
    conn = create_db_connection()
    customers = load_customers_from_db(conn)
    print(f"✅ Loaded {len(customers)} customers from prod_source")

    producer = create_kafka_producer()
    print("✅ Connected to Redpanda on localhost:9092")
    print("✅ Connected to Postgres (prod_source)")
    print("🚀 Streaming transactions...\n")

    try:
        count = 0
        while True:
            txn = generate_transaction(customers)
            txn_dict = txn.model_dump(mode="json")

            # Simultaneous: write to DB + push to Redpanda
            write_to_db(conn, txn_dict)
            producer.send("transactions", value=txn_dict)

            count += 1
            print(
                f"[{count}] {txn.payment_channel.value} | "
                f"{txn.amount} EUR | {txn.sender_iban[:8]}... | "
                f"DB ✓ | Redpanda ✓"
            )
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n⏹ Stopped after {count} transactions")
    finally:
        producer.flush()
        producer.close()
        conn.close()