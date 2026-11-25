-- Exactly one current row per product_id
SELECT product_id, COUNT(*) AS current_cnt
FROM {{ ref('dim_product') }}
WHERE is_current
GROUP BY product_id
HAVING COUNT(*) <> 1
