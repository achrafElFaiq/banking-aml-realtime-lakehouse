WITH cross_border_rolling AS (
    SELECT
        t1.sender_iban_hmac,
        t1.sender_iban_truncated,
        t1.transaction_id,
        t1.amount_eur,
        t1.executed_at,
        SUM(t2.amount_eur) AS rolling_30d_cross_border_eur
    FROM {{ ref('int_reconciled_transactions') }} AS t1
    INNER JOIN {{ ref('int_reconciled_transactions') }} AS t2
        ON
            t1.sender_iban_hmac = t2.sender_iban_hmac
            AND t2.is_cross_border = TRUE
            AND t2.final_status != 'BLOCKED'
            AND t2.executed_at::TIMESTAMP BETWEEN
            DATEADD('day', -30, t1.executed_at::TIMESTAMP)
            AND t1.executed_at::TIMESTAMP
    WHERE
        t1.is_cross_border = TRUE
        AND t1.final_status != 'BLOCKED'
    GROUP BY t1.sender_iban_hmac, t1.sender_iban_truncated, t1.transaction_id, t1.amount_eur, t1.executed_at
)

SELECT
    r.transaction_id,
    r.sender_iban_hmac,
    r.sender_iban_truncated,
    c.customer_id,
    c.risk_tier,
    r.amount_eur,
    r.executed_at,
    r.rolling_30d_cross_border_eur,
    'CUMULATIVE_CROSS_BORDER_10K' AS rule_code,
    CURRENT_TIMESTAMP AS detected_at
FROM cross_border_rolling AS r
LEFT JOIN {{ ref('stg_customers') }} AS c
    ON r.sender_iban_hmac = c.iban_hmac
WHERE r.rolling_30d_cross_border_eur > 10000
