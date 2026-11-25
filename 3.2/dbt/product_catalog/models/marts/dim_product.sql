{{ config(materialized='table') }}

WITH snap AS (
    SELECT *
    FROM {{ ref('product_snapshot') }}
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['product_id', 'dbt_valid_from']) }} AS product_sk,
    product_id,
    name,
    category,
    price,
    description,
    updated_at,
    dbt_valid_from AS valid_from,
    dbt_valid_to AS valid_to,
    CASE WHEN dbt_valid_to IS NULL THEN TRUE ELSE FALSE END AS is_current
FROM snap
