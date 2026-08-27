"""Generate synthetic transaction events mimicking a French banking payment gateway."""

import random
import uuid
from datetime import datetime
from enum import Enum

from faker import Faker
from pydantic import BaseModel

from generators.customers import Customer

fake = Faker("fr_FR")
fake_foreign = Faker(["de_DE", "es_ES", "it_IT", "nl_NL"])

Faker.seed(42)
random.seed(42)

CROSS_BORDER_RATIO = 0.3
CHANNEL_WEIGHTS = [40, 10, 50]  # SEPA, INSTANT_SEPA, CARD


class PaymentChannel(str, Enum):
    """Payment channel types in French banking."""

    SEPA = "SEPA"
    INSTANT_SEPA = "INSTANT_SEPA"
    CARD = "CARD"


class Transaction(BaseModel):
    """Schema for a banking transaction event."""

    transaction_id: str
    sender_iban: str
    beneficiary_iban: str
    amount: str
    currency: str
    payment_channel: PaymentChannel
    executed_at: datetime


def _generate_amount() -> str:
    """Generate a realistic EUR amount in European comma format."""
    # Small transactions (coffee, lunch) are most common
    # Large transfers (rent, savings) are rare
    roll = random.random()
    if roll < 0.60:
        amount = round(random.uniform(5, 150), 2)
    elif roll < 0.85:
        amount = round(random.uniform(150, 2000), 2)
    elif roll < 0.95:
        amount = round(random.uniform(2000, 8000), 2)
    else:
        amount = round(random.uniform(8000, 15000), 2)

    # European format: comma as decimal separator
    return f"{amount:.2f}".replace(".", ",")


def generate_transaction(customers: list[Customer]) -> Transaction:
    """Generate one synthetic transaction referencing an existing customer."""
    sender = random.choice(customers)

    # 30% cross-border, 70% domestic
    if random.random() < CROSS_BORDER_RATIO:
        beneficiary_iban = fake_foreign.iban()
    else:
        beneficiary_iban = fake.iban()
        while beneficiary_iban == sender.iban:
            beneficiary_iban = fake.iban()

    channel = random.choices(list(PaymentChannel), weights=CHANNEL_WEIGHTS, k=1)[0]

    return Transaction(
        transaction_id=str(uuid.uuid4()),
        sender_iban=sender.iban,
        beneficiary_iban=beneficiary_iban,
        amount=_generate_amount(),
        currency="EUR",
        payment_channel=channel,
        executed_at=fake.date_time_between(start_date="-7d", end_date="now"),
    )


if __name__ == "__main__":
    from generators.customers import generate_customers

    customer_pool = generate_customers(100)
    for _ in range(5):
        txn = generate_transaction(customer_pool)
        print(txn.model_dump_json(indent=2))