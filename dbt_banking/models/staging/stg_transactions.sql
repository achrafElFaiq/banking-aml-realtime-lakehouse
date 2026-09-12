SELECT
    transaction_id,
    sender_iban,
    beneficiary_iban,
    CAST(
        REPLACE(REPLACE(amount, '.', ''), ',', '.') AS DECIMAL(18, 2)
    ) AS amount_eur,
    currency,
    payment_channel,
    status,
    blocked_reason,
    executed_at,
    LEFT(beneficiary_iban, 2) != 'FR' AS is_cross_border,
    ingested_at
FROM {{ ref('raw_transactions') }}