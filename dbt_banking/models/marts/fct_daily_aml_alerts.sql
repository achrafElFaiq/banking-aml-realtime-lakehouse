WITH cross_border_rolling AS (
    SELECT
        sender_iban,
        transaction_id,
        amount_eur,
        executed_at,
        SUM(amount_eur) OVER (
            PARTITION BY sender_iban
            ORDER BY executed_at
            RANGE BETWEEN INTERVAL '30 days' PRECEDING AND CURRENT ROW
        ) AS rolling_30d_cross_border_eur
    FROM {{ ref('int_reconciled_transactions') }}
    WHERE is_cross_border = TRUE
      AND final_status != 'BLOCKED'
)

SELECT
    r.transaction_id,
    r.sender_iban,
    c.customer_id,
    c.risk_tier,
    r.amount_eur,
    r.executed_at,
    r.rolling_30d_cross_border_eur,
    'CUMULATIVE_CROSS_BORDER_10K' AS rule_code,
    CURRENT_TIMESTAMP AS detected_at
FROM cross_border_rolling r
LEFT JOIN {{ ref('stg_customers') }} c
    ON r.sender_iban = c.iban
WHERE r.rolling_30d_cross_border_eur > 10000