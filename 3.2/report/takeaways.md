# HW 3.2 — Takeaways and extension

Evidence: `report/evidence/`.

## Five takeaways

1. **Clones copy metadata, not a full second copy of the data.** After `CREATE DATABASE dev_product_catalog CLONE product_catalog`, row counts matched production right away. Building `dim_product_rated` only in the clone left production unchanged (`clone_dev_rated.txt`, `clone_databases.txt`).

2. **Trial Time Travel is only 1 day.** A `2023-12-31` clone fails on this account (`time_travel_retention.txt`). I cloned at a recent timestamp instead. Live `HD-00001` has two versions; the PIT clone still has one (`clone_point_in_time.txt`).

3. **`updated_at` has to move for the timestamp snapshot strategy.** I changed price/category on 25 products and bumped only those timestamps. The second build gave those ids two `dim_product` rows; unchanged ids stayed at one current row (`scd_acceptance.txt`).

4. **dbt failed the build when tests failed; Airflow failed early on a bad extract.** Extract checks for a missing/empty CSV. `verify_row_counts` fails if raw or dim is empty (`airflow_etl_run_log.txt`).

5. **Daily `CREATE OR REPLACE DATABASE … CLONE` would wipe a working sandbox.** That is why clones are in a separate DAG (`product_catalog_clones`) instead of on the daily ETL schedule.

## Extension

Add a sales fact table that stores `product_sk` and join it to `dim_product` so reports can use product attributes as of the sale date. Also run `dbt build` against a fresh clone in CI before promoting to production.
