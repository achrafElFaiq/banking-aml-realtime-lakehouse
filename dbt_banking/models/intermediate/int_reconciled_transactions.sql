SELECT
    COALESCE(t.transaction_id, s.transaction_id) AS transaction_id,
    COALESCE(t.sender_iban, s.sender_iban) AS sender_iban,
    COALESCE(t.beneficiary_iban, s.beneficiary_iban) AS beneficiary_iban,

    -- Settlement amount is the official truth
    COALESCE(s.amount_eur, t.amount_eur) AS amount_eur,

    COALESCE(t.currency, s.currency) AS currency,
    COALESCE(t.payment_channel, s.payment_channel) AS payment_channel,

    -- Status logic: BLOCKED always wins, then SETTLED, then PENDING
    CASE
        WHEN t.status = 'BLOCKED' THEN 'BLOCKED'
        WHEN s.transaction_id IS NOT NULL THEN 'SETTLED'
        ELSE t.status
    END AS final_status,

    t.blocked_reason,

    COALESCE(t.executed_at, s.executed_at) AS executed_at,
    COALESCE(t.is_cross_border, s.is_cross_border) AS is_cross_border,

    -- Track data lineage
    t.transaction_id IS NOT NULL AS seen_in_stream,
    s.transaction_id IS NOT NULL AS seen_in_settlement

FROM {{ ref('stg_transactions') }} t
FULL OUTER JOIN {{ ref('stg_settlements') }} s
    USING (transaction_id)