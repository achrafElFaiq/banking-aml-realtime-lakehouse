"""Consumer: reads transaction events from Redpanda, applies velocity rules,
and updates the prod database if fraud is detected.

This is Layer 2 (Real-time detection) of the Lambda architecture.
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta

import psycopg2
from kafka import KafkaConsumer

# Rule configuration — in a production system this lives in rules.yaml
VELOCITY_RULE = {
    "name": "VELOCITY_RULE",
    "description": "5+ INSTANT_SEPA in 60 min for HIGH/PEP customer",
    "max_transactions": 5,
    "window_minutes": 60,
    "channels": ["INSTANT_SEPA"],
    "risk_tiers": ["HIGH", "PEP"],
}


def create_consumer() -> KafkaConsumer:
    """Create a Kafka consumer connected to Redpanda."""
    return KafkaConsumer(
        "transactions",
        bootstrap_servers=["localhost:9092"],
        group_id="aml-velocity-checker",
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
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


def load_customer_risk_tiers(conn: psycopg2.extensions.connection) -> dict[str, str]:
    """Load IBAN → risk_tier mapping from the database."""
    cur = conn.cursor()
    cur.execute("SELECT iban, risk_tier FROM prod_source.customers")
    return {row[0]: row[1] for row in cur.fetchall()}


def block_transaction(
    conn: psycopg2.extensions.connection,
    transaction_id: str,
    reason: str,
) -> None:
    """Update a transaction status to BLOCKED with a reason."""
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE prod_source.transactions
        SET status = 'BLOCKED', blocked_reason = %s
        WHERE transaction_id = %s
        """,
        (reason, transaction_id),
    )
    conn.commit()


def check_velocity_rule(
    txn: dict,
    risk_tiers: dict[str, str],
    window: dict[str, list[datetime]],
) -> str | None:
    """Check if a transaction triggers the velocity rule.

    Returns the blocked_reason string if triggered, None otherwise.
    """
    sender_iban = txn["sender_iban"]
    channel = txn["payment_channel"]

    # Only check INSTANT_SEPA
    if channel not in VELOCITY_RULE["channels"]:
        return None

    # Only check HIGH/PEP customers
    risk_tier = risk_tiers.get(sender_iban)
    if risk_tier not in VELOCITY_RULE["risk_tiers"]:
        return None

    # Parse transaction time and add to window
    executed_at = datetime.fromisoformat(txn["executed_at"])
    window[sender_iban].append(executed_at)

    # Remove events older than 60 minutes
    cutoff = executed_at - timedelta(minutes=VELOCITY_RULE["window_minutes"])
    window[sender_iban] = [t for t in window[sender_iban] if t > cutoff]

    # Check threshold
    event_count = len(window[sender_iban])
    if event_count >= VELOCITY_RULE["max_transactions"]:
        return (
            f"VELOCITY_RULE: {event_count} INSTANT_SEPA in "
            f"{VELOCITY_RULE['window_minutes']} min | "
            f"risk_tier={risk_tier}"
        )

    return None


if __name__ == "__main__":
    conn = create_db_connection()
    risk_tiers = load_customer_risk_tiers(conn)
    print(f"✅ Loaded {len(risk_tiers)} customer risk tiers")

    consumer = create_consumer()
    print("✅ Connected to Redpanda")
    print("👁 Watching for suspicious transactions...\n")

    # Rolling window: tracks recent INSTANT_SEPA per customer
    velocity_window: dict[str, list[datetime]] = defaultdict(list)

    try:
        blocked_count = 0
        total_count = 0

        for message in consumer:
            txn = message.value
            total_count += 1

            reason = check_velocity_rule(txn, risk_tiers, velocity_window)

            if reason:
                block_transaction(conn, txn["transaction_id"], reason)
                blocked_count += 1
                print(
                    f"🚨 [{total_count}] BLOCKED | {txn['sender_iban'][:10]}... | {reason}"
                )
            else:
                print(
                    f"   [{total_count}] OK | {txn['payment_channel']} | "
                    f"{txn['amount']} EUR | {txn['sender_iban'][:10]}..."
                )

    except KeyboardInterrupt:
        print(f"\n⏹ Processed {total_count} transactions, blocked {blocked_count}")
    finally:
        consumer.close()
        conn.close()