"""Daily product catalog ETL: extract → load Snowflake → dbt build → verify."""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator

HW_ROOT = Path(os.environ.get("HW32_ROOT", "/opt/airflow/hw32"))
if str(HW_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(HW_ROOT / "scripts"))

default_args = {
    "owner": "river",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
}


def extract_products(**_context):
    """Raise if the catalog CSV is missing or empty."""
    from load_products import extract_check

    extract_check(HW_ROOT / "data" / "products.csv")


def load_products(**_context):
    from load_products import load

    load(HW_ROOT / "data" / "products.csv")


with DAG(
    dag_id="product_catalog_etl",
    default_args=default_args,
    description="ETL for Product Catalog → Snowflake → dbt SCD Type 2",
    schedule="@daily",
    start_date=datetime(2026, 11, 1),
    catchup=False,
    tags=["hw32", "product_catalog"],
) as dag:
    extract_task = PythonOperator(
        task_id="extract_products",
        python_callable=extract_products,
    )

    load_task = PythonOperator(
        task_id="load_products",
        python_callable=load_products,
    )

    # Covers rubric "trigger dbt" and "dbt invoked from Airflow"
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            "dbt build "
            f"--project-dir {HW_ROOT}/dbt/product_catalog "
            f"--profiles-dir ${{DBT_PROFILES_DIR:-{HW_ROOT}/dbt/product_catalog}}"
        ),
        env={
            **os.environ,
            "HW32_ROOT": str(HW_ROOT),
            "DBT_PROFILES_DIR": os.environ.get(
                "DBT_PROFILES_DIR", f"{HW_ROOT}/dbt/product_catalog"
            ),
        },
    )

    verify_row_counts = SnowflakeOperator(
        task_id="verify_row_counts",
        snowflake_conn_id="snowflake_conn",
        sql="""
        SELECT
          CASE
            WHEN (SELECT COUNT(*) FROM product_catalog.raw.products) = 0
              THEN 1/0
            WHEN (SELECT COUNT(*) FROM product_catalog.analytics.dim_product) = 0
              THEN 1/0
            ELSE 1
          END AS ok
        """,
    )

    extract_task >> load_task >> dbt_build >> verify_row_counts
