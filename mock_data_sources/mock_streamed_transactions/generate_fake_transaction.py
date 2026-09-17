"""Generate synthetic transaction events mimicking a French banking payment gateway."""

import random
import uuid
from datetime import datetime
from enum import Enum

from faker import Faker
from pydantic import BaseModel

from mock_data_sources.mock_prod_db.generate_fake_customers import Customer

fake = Faker("fr_FR")
fake_foreign = Faker(["de_DE", "es_ES", "it_IT", "nl_NL"])

Faker.seed(42)
random.seed(42)

CROSS_BORDER_RATIO = 0.3
CHANNEL_WEIGHTS = [40, 10, 50]  # SEPA, INSTANT_SEPA, CARD

# Fraud scenario probabilities
VELOCITY_BURST_PROBABILITY = 0.02  # 2% chance per tick
LARGE_CROSS_BORDER_PROBABILITY = 0.05  # 5% chance per tick


class PaymentChannel(str, Enum):
    SEPA = "SEPA"
    INSTANT_SEPA = "INSTANT_SEPA"
    CARD = "CARD"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    SETTLED = "SETTLED"
    BLOCKED = "BLOCKED"


class Transaction(BaseModel):
    transaction_id: str
    sender_iban: str
    beneficiary_iban: str
    amount: str
    currency: str
    payment_channel: PaymentChannel
    status: TransactionStatus = TransactionStatus.PENDING
    blocked_reason: str | None = None
    executed_at: datetime


def _generate_amount() -> str:
    roll = random.random()
    if roll < 0.60:
        amount = round(random.uniform(5, 150), 2)
    elif roll < 0.85:
        amount = round(random.uniform(150, 2000), 2)
    elif roll < 0.95:
        amount = round(random.uniform(2000, 8000), 2)
    else:
        amount = round(random.uniform(8000, 15000), 2)
    return f"{amount:.2f}".replace(".", ",")


def _pick_beneficiary(sender_iban: str, force_cross_border: bool = False) -> str:
    if force_cross_border or random.random() < CROSS_BORDER_RATIO:
        return fake_foreign.iban()
    else:
        iban = fake.iban()
        while iban == sender_iban:
            iban = fake.iban()
        return iban


def generate_transaction(customers: list[Customer]) -> list[Transaction]:
    """Generate one or more transactions. Returns a list.

    Normally returns 1 transaction. Occasionally returns a burst
    of 6+ INSTANT_SEPA from a HIGH/PEP customer (velocity fraud).
    """
    # 2% chance: velocity burst from HIGH/PEP customer
    if random.random() < VELOCITY_BURST_PROBABILITY:
        return _generate_velocity_burst(customers)

    # 5% chance: large cross-border transfer (feeds cumulative rule)
    if random.random() < LARGE_CROSS_BORDER_PROBABILITY:
        return [_generate_large_cross_border(customers)]

    # Normal transaction
    return [_generate_normal(customers)]


def _generate_normal(customers: list[Customer]) -> Transaction:
    sender = random.choice(customers)
    channel = random.choices(list(PaymentChannel), weights=CHANNEL_WEIGHTS, k=1)[0]

    return Transaction(
        transaction_id=str(uuid.uuid4()),
        sender_iban=sender.iban,
        beneficiary_iban=_pick_beneficiary(sender.iban),
        amount=_generate_amount(),
        currency="EUR",
        payment_channel=channel,
        executed_at=datetime.now(),
    )


def _generate_velocity_burst(customers: list[Customer]) -> list[Transaction]:
    """6 INSTANT_SEPA in rapid succession from a HIGH/PEP customer."""
    high_risk = [c for c in customers if c.risk_tier in ("HIGH", "PEP")]
    if not high_risk:
        return [_generate_normal(customers)]

    sender = random.choice(high_risk)
    transactions = []

    for _ in range(6):
        txn = Transaction(
            transaction_id=str(uuid.uuid4()),
            sender_iban=sender.iban,
            beneficiary_iban=_pick_beneficiary(sender.iban, force_cross_border=True),
            amount=f"{round(random.uniform(1000, 4000), 2):.2f}".replace(".", ","),
            currency="EUR",
            payment_channel=PaymentChannel.INSTANT_SEPA,
            executed_at=datetime.now(),
        )
        transactions.append(txn)

    return transactions


def _generate_large_cross_border(customers: list[Customer]) -> Transaction:
    """Single large cross-border transfer that feeds the cumulative €10k rule."""
    sender = random.choice(customers)

    return Transaction(
        transaction_id=str(uuid.uuid4()),
        sender_iban=sender.iban,
        beneficiary_iban=fake_foreign.iban(),
        amount=f"{round(random.uniform(3000, 9000), 2):.2f}".replace(".", ","),
        currency="EUR",
        payment_channel=PaymentChannel.SEPA,
        executed_at=datetime.now(),
    )


if __name__ == "__main__":
    from mock_data_sources.mock_prod_db.generate_fake_customers import generate_customers

    customer_pool = generate_customers(100)
    for _ in range(10):
        txns = generate_transaction(customer_pool)
        for txn in txns:
            print(txn.model_dump_json(indent=2))