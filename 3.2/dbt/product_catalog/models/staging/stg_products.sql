{{ config(materialized='view') }}

WITH source AS (
    SELECT *
    FROM {{ source('raw', 'products') }}
),

cleaned AS (
    SELECT
        TRIM(product_id) AS product_id,
        TRIM(name) AS name,
        TRIM(category) AS category,
        TRY_TO_NUMBER(price, 10, 2) AS price,
        description,
        updated_at::TIMESTAMP_NTZ AS updated_at
    FROM source
    WHERE product_id IS NOT NULL
      AND TRIM(product_id) <> ''
),

deduped AS (
    SELECT *
    FROM cleaned
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY product_id
        ORDER BY updated_at DESC NULLS LAST
    ) = 1
)

SELECT * FROM deduped
