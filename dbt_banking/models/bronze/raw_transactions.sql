SELECT
    transaction_id,
    sender_iban,
    beneficiary_iban,
    amount,
    currency,
    payment_channel,
    status,
    blocked_reason,
    executed_at,
    CURRENT_TIMESTAMP AS ingested_at
FROM {{ source('prod_source', 'transactions') }}