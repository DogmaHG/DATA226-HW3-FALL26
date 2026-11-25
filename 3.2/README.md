# HW 3.2 — E-commerce Product Catalog

Local CSV → Airflow → Snowflake staging → dbt snapshot (SCD Type 2) → zero-copy clones.

**Grading delivery:** Canvas gets the IEEE PDF write-up; this repository holds the code and evidence.

- Repo: https://github.com/DogmaHG/DATA226-HW3-FALL26
- PDF: `submission/HW32_River_Roseveare-Hunt.pdf` (also under `3.2/report/hw32_ieee.pdf`)

## Layout

| Path | Role |
|------|------|
| `airflow/dags/` | `product_catalog_etl.py`, `product_catalog_clones.py` |
| `dbt/product_catalog/` | staging, snapshot, `dim_product`, tests, prototype model |
| `sql/` | Snowflake setup / acceptance / clone sketches |
| `scripts/` | load, mutate, acceptance, clones, Airflow CLI twin |
| `data/` | `products.csv`, `products_v1.csv`, `SOURCE.md` |
| `report/evidence/` | SCD, Airflow, and clone query dumps |
| `report/takeaways.md` | Five takeaways + extension |
| `llm-use-log.md` | Mandatory AI disclosure |

## Run locally

1. Copy `.env.example` → `.env`. Google SSO trials: use a Programmatic Access Token as `SNOWFLAKE_PASSWORD`.
2. Create a venv, install deps (`dbt-core`, `dbt-snowflake`, `snowflake-connector-python`, Airflow as needed).
3. From `3.2/`:

```bash
source .venv/bin/activate
./scripts/run_pipeline.sh
python scripts/run_airflow_tasks.py
```
