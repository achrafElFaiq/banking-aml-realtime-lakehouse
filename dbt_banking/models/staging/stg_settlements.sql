SELECT
    transaction_id,
    {{ pseudonymize_iban('sender_iban') }} AS sender_iban_hmac,
    {{ truncate_iban('sender_iban') }} AS sender_iban_truncated,
    {{ pseudonymize_iban('beneficiary_iban') }} AS beneficiary_iban_hmac,
    {{ truncate_iban('beneficiary_iban') }} AS beneficiary_iban_truncated,
    CAST(
        REPLACE(REPLACE(amount, '.', ''), ',', '.') AS DECIMAL(18, 2)
    ) AS amount_eur,
    currency,
    payment_channel,
    status,
    blocked_reason,
    executed_at,
    LEFT(beneficiary_iban, 2) != 'FR' AS is_cross_border,
    loaded_at AS ingested_at
FROM {{ source('bronze', 'raw_settlements') }}
