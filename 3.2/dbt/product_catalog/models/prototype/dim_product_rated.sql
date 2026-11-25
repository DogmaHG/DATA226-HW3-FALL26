{{
  config(
    materialized='table',
    enabled=true,
  )
}}

-- Dev/prototype: rating derived from description length
SELECT
    product_sk,
    product_id,
    name,
    category,
    price,
    description,
    valid_from,
    valid_to,
    is_current,
    LEAST(5.0, GREATEST(1.0, ROUND(LENGTH(description) / 40.0, 1))) AS product_rating,
    CASE
        WHEN price < 25 THEN 'budget'
        WHEN price < 100 THEN 'mid'
        ELSE 'premium'
    END AS price_band
FROM {{ ref('dim_product') }}
WHERE is_current
