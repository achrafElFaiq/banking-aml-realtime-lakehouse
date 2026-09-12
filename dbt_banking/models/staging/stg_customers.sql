SELECT
    customer_id,
    first_name,
    last_name,
    email,
    phone_number,
    iban,
    address,
    city,
    country,
    risk_tier,
    created_at,
    ingested_at
FROM {{ ref('raw_customers') }}