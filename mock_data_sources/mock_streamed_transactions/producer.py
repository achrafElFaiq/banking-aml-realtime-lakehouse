"""Producer: generates synthetic transactions and pushes them to Redpanda."""

import json
import time

from kafka import KafkaProducer

from generators.customers import generate_customers
from generators.stream_transactions import generate_transaction


def create_producer() -> KafkaProducer:
    """Create a Kafka producer connected to Redpanda."""
    return KafkaProducer(
        bootstrap_servers=["localhost:9092"],
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
    )


if __name__ == "__main__":
    # Load customer pool once — all transactions reference these customers
    customers = generate_customers(500)
    print(f"✅ Generated {len(customers)} customers")

    producer = create_producer()
    print("✅ Connected to Redpanda on localhost:9092")
    print("🚀 Streaming transactions...\n")

    try:
        count = 0
        while True:
            txn = generate_transaction(customers)
            producer.send("transactions", value=txn.model_dump(mode="json"))
            count += 1
            print(f"[{count}] {txn.payment_channel.value} | {txn.amount} EUR | {txn.sender_iban[:8]}...")
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n⏹ Stopped after {count} transactions")
    finally:
        producer.flush()
        producer.close()