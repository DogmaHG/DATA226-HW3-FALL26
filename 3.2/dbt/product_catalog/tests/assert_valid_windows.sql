-- No inverted validity windows
SELECT product_id, product_sk, valid_from, valid_to
FROM {{ ref('dim_product') }}
WHERE valid_to IS NOT NULL
  AND valid_to <= valid_from
