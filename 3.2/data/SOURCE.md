# Source dataset

| Field | Value |
|-------|-------|
| Suggested source | [Home Depot products on Kaggle](https://www.kaggle.com/datasets/thedevastator/the-home-depot-products-dataset) |
| File used | `products.csv` (local) |
| Notes | Local sample catalog with stable product ids (full Kaggle dump not required for the pipeline). |
| Created | 2026-11-25 |
| Row count | 3,000 (+ header) |
| Natural key | `product_id` (`HD-00001` … `HD-03000`) |
| Columns | `product_id`, `name`, `category`, `price`, `description`, `updated_at` |
| Version 1 copy | `products_v1.csv` |

`updated_at` supports the dbt snapshot `timestamp` strategy.
