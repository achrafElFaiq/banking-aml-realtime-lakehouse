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
    CURRENT_TIMESTAMP AS ingested_at
FROM {{ source('prod_source', 'customers') }}