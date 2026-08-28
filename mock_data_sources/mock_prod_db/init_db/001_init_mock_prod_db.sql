-- ============================================================
-- MOCK PRODUCTION DATABASE
-- Simulates the bank's core operational system.
-- This is NOT our analytics platform — it's the source system
-- that our lakehouse reads from.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS prod_source;

-- Bank's customer master table
CREATE TABLE IF NOT EXISTS prod_source.customers (
    customer_id     VARCHAR(36) PRIMARY KEY,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(255),
    phone_number    VARCHAR(30),
    iban            VARCHAR(34) NOT NULL UNIQUE,
    address         VARCHAR(500),
    city            VARCHAR(100),
    country         VARCHAR(5) DEFAULT 'FR',
    risk_tier       VARCHAR(10) NOT NULL,
    created_at      TIMESTAMP NOT NULL
);

-- Bank's transaction ledger
-- Our analytics platform never reads from this table directly.
-- Transactions reach us through the payment gateway (Redpanda stream).
-- This table exists because a real prod DB would have it.
CREATE TABLE IF NOT EXISTS prod_source.transactions (
    transaction_id      VARCHAR(36) PRIMARY KEY,
    sender_iban         VARCHAR(34) NOT NULL,
    beneficiary_iban    VARCHAR(34) NOT NULL,
    amount              VARCHAR(20) NOT NULL,
    currency            VARCHAR(3) NOT NULL,
    payment_channel     VARCHAR(20) NOT NULL,
    status              VARCHAR(10) NOT NULL DEFAULT 'PENDING',
    blocked_reason      VARCHAR(255),
    executed_at         TIMESTAMP NOT NULL
);