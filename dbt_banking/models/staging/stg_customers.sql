SELECT
    customer_id,
    first_name,
    last_name,
    email,
    phone_number,
    {{ pseudonymize_iban('iban') }} AS iban_hmac,
    {{ truncate_iban('iban') }} AS iban_truncated,
    address,
    city,
    country,
    risk_tier,
    created_at,
    ingested_at
FROM {{ source('bronze', 'raw_customers') }}
