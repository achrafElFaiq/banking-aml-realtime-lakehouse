{% snapshot snap_customers %}

{{
    config(
        target_schema='GOLD',
        unique_key='customer_id',
        strategy='check',
        check_cols=['risk_tier', 'address', 'city'],
    )
}}

SELECT
    customer_id,
    {{ pseudonymize_iban('iban') }} AS iban_hmac,
    {{ truncate_iban('iban') }} AS iban_truncated,
    address,
    city,
    country,
    risk_tier,
    created_at
FROM {{ source('bronze', 'raw_customers') }}

{% endsnapshot %}