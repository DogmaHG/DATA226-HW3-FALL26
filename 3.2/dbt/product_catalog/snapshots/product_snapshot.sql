{% snapshot product_snapshot %}
{{
    config(
      target_schema='snapshots',
      strategy='timestamp',
      unique_key='product_id',
      updated_at='updated_at',
    )
}}

SELECT
    product_id,
    name,
    category,
    price,
    description,
    updated_at
FROM {{ ref('stg_products') }}

{% endsnapshot %}
