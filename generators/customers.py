"""Generate synthetic customer data mimicking a French core banking system."""

import csv
import random
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path

from faker import Faker
from pydantic import BaseModel

fake = Faker("fr_FR")

# Seed for reproducibility — same data every run, important for testing
Faker.seed(42)
random.seed(42)


class RiskTier(str, Enum):
    """Customer AML risk classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    PEP = "PEP"


RISK_WEIGHTS = [70, 20, 7, 3]


class Customer(BaseModel):
    """Schema for a core banking customer record."""

    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    iban: str
    address: str
    city: str
    country: str
    risk_tier: RiskTier
    created_at: datetime


def generate_customers(n: int) -> list[Customer]:
    """Generate n synthetic French bank customers with weighted risk tiers."""
    customers: list[Customer] = []

    for _ in range(n):
        risk_tier = random.choices(list(RiskTier), weights=RISK_WEIGHTS, k=1)[0]

        customer = Customer(
            customer_id=str(uuid.uuid4()),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.email(),
            phone_number=fake.phone_number(),
            iban=fake.iban(),
            address=fake.address().replace("\n", ", "),
            city=fake.city(),
            country="FR",
            risk_tier=risk_tier,
            created_at=fake.date_time_between(start_date="-2y", end_date="now"),
        )
        customers.append(customer)

    return customers


def save_to_csv(customers: list[Customer], path: Path) -> None:
    """Write customer list to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(Customer.model_fields.keys()))
        writer.writeheader()
        for customer in customers:
            writer.writerow(customer.model_dump())


if __name__ == "__main__":
    output_path = Path("data/customers.csv")
    generated = generate_customers(500)

    for c in generated[:3]:
        print(c.model_dump_json(indent=2))

    save_to_csv(generated, output_path)
    print(f"\n{len(generated)} customers saved to {output_path}")