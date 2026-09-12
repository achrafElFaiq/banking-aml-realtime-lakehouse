{% snapshot snap_customers %}

{{
    config(
        target_schema='gold',
        unique_key='customer_id',
        strategy='check',
        check_cols=['risk_tier', 'address', 'city'],
    )
}}

SELECT
    customer_id,
    first_name,
    last_name,
    iban,
    address,
    city,
    country,
    risk_tier,
    created_at
FROM {{ source('prod_source', 'customers') }}

{% endsnapshot %}