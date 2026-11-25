{{ config(materialized='view', enabled=false) }}

-- Optional analysis helper: enable against a point-in-time clone target.
-- Live vs PIT comparison is also documented via sql/03_clones.sql queries.
SELECT
    COUNT(*) AS current_product_count
FROM {{ ref('dim_product') }}
WHERE is_current
