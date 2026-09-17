{% macro pseudonymize_iban(column_name) %}
    SHA2(CONCAT('{{ var("hmac_secret_key", "aml-secret-2026") }}', {{ column_name }}), 256)
{% endmacro %}

{% macro truncate_iban(column_name) %}
    LEFT({{ column_name }}, 4) || '****' || RIGHT({{ column_name }}, 4)
{% endmacro %}