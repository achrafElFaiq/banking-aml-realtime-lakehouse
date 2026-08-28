"""Populate the mock production database with synthetic customers."""

import psycopg2

from mock_data_sources.mock_prod_db.generate_fake_customers import generate_customers


def load_customers(n: int = 500) -> None:
    """Generate n customers and insert into prod_source.customers."""
    customers = generate_customers(n)

    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="aml_lakehouse",
        user="aml",
        password="aml_secret",
    )

    try:
        cur = conn.cursor()
        for c in customers:
            cur.execute(
                """
                INSERT INTO prod_source.customers
                    (customer_id, first_name, last_name, email, phone_number,
                     iban, address, city, country, risk_tier, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO NOTHING
                """,
                (
                    c.customer_id,
                    c.first_name,
                    c.last_name,
                    c.email,
                    c.phone_number,
                    c.iban,
                    c.address,
                    c.city,
                    c.country,
                    c.risk_tier.value,
                    c.created_at,
                ),
            )
        conn.commit()
        print(f"✅ {len(customers)} customers loaded into prod_source.customers")
    finally:
        conn.close()


if __name__ == "__main__":
    load_customers()