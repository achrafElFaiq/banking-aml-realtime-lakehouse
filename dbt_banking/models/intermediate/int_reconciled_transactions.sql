SELECT
    COALESCE(t.transaction_id, s.transaction_id) AS transaction_id,
    COALESCE(t.sender_iban_hmac, s.sender_iban_hmac) AS sender_iban_hmac,
    COALESCE(t.sender_iban_truncated, s.sender_iban_truncated) AS sender_iban_truncated,
    COALESCE(t.beneficiary_iban_hmac, s.beneficiary_iban_hmac) AS beneficiary_iban_hmac,
    COALESCE(t.beneficiary_iban_truncated, s.beneficiary_iban_truncated) AS beneficiary_iban_truncated,
    COALESCE(s.amount_eur, t.amount_eur) AS amount_eur,
    COALESCE(t.currency, s.currency) AS currency,
    COALESCE(t.payment_channel, s.payment_channel) AS payment_channel,

    CASE
        WHEN t.status = 'BLOCKED' THEN 'BLOCKED'
        WHEN s.transaction_id IS NOT NULL THEN 'SETTLED'
        ELSE t.status
    END AS final_status,

    t.blocked_reason,
    COALESCE(t.executed_at, s.executed_at) AS executed_at,
    COALESCE(t.is_cross_border, s.is_cross_border) AS is_cross_border,
    t.transaction_id IS NOT NULL AS seen_in_stream,
    s.transaction_id IS NOT NULL AS seen_in_settlement

FROM {{ ref('stg_transactions') }} AS t
FULL OUTER JOIN {{ ref('stg_settlements') }} AS s
    ON t.transaction_id = s.transaction_id
