#!/usr/bin/env bash
# End-to-end CLI pipeline for HW 3.2 (phases 1–3, then optional clones).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate
set -a
# shellcheck disable=SC1091
source .env
set +a

export DBT_PROFILES_DIR="${DBT_PROFILES_DIR:-$ROOT/dbt/product_catalog}"
export PYTHONPATH="$ROOT/scripts${PYTHONPATH:+:$PYTHONPATH}"

echo "=== Phase 1: setup + load v1 ==="
python scripts/setup_snowflake.py
cp data/products_v1.csv data/products.csv
python scripts/load_products.py

echo "=== Phase 2: dbt deps + build (v1) ==="
dbt deps --project-dir dbt/product_catalog --profiles-dir "$DBT_PROFILES_DIR"
dbt build --project-dir dbt/product_catalog --profiles-dir "$DBT_PROFILES_DIR"

echo "=== Phase 3: mutate + reload + rebuild ==="
python scripts/mutate_products.py
python scripts/load_products.py
dbt build --project-dir dbt/product_catalog --profiles-dir "$DBT_PROFILES_DIR"
python scripts/run_acceptance.py

echo "=== Phase 5: clones ==="
python scripts/run_clones.py

echo "Pipeline complete. Evidence under report/evidence/"
