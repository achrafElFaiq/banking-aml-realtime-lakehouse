SELECT
    t.transaction_id,
    t.sender_iban,
    t.beneficiary_iban,
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
FROM {{ ref('int_reconciled_transactions') }} t
LEFT JOIN {{ ref('stg_customers') }} c
    ON t.sender_iban = c.iban