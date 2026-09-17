SELECT
    t.transaction_id,
    t.sender_iban_hmac,
    t.sender_iban_truncated,
    t.beneficiary_iban_hmac,
    t.beneficiary_iban_truncated,
    t.amount_eur,
    t.currency,
    t.payment_channel,
    t.final_status,
    t.blocked_reason,
    t.executed_at,
    t.is_cross_border,
    t.seen_in_stream,
    t.seen_in_settlement,
    c.customer_id,
    c.risk_tier
FROM {{ ref('int_reconciled_transactions') }} AS t
LEFT JOIN {{ ref('stg_customers') }} AS c
    ON t.sender_iban_hmac = c.iban_hmac
