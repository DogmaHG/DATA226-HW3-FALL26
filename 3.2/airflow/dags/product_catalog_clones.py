"""Manual DAG for Snowflake zero-copy cloning demos (separate from daily load)."""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator

HW_ROOT = Path(os.environ.get("HW32_ROOT", "/opt/airflow/hw32"))
_PROFILES = os.environ.get("DBT_PROFILES_DIR", f"{HW_ROOT}/dbt/product_catalog")
DBT = f"dbt --project-dir {HW_ROOT}/dbt/product_catalog --profiles-dir {_PROFILES}"

default_args = {
    "owner": "river",
    "depends_on_past": False,
    "retries": 0,
    "email_on_failure": False,
}

with DAG(
    dag_id="product_catalog_clones",
    default_args=default_args,
    description="Zero-copy clone demos for HW 3.2",
    schedule=None,
    start_date=datetime(2026, 11, 1),
    catchup=False,
    tags=["hw32", "clones"],
) as dag:
    clone_dev_database = SnowflakeOperator(
        task_id="clone_dev_database",
        snowflake_conn_id="snowflake_conn",
        sql="CREATE OR REPLACE DATABASE dev_product_catalog CLONE product_catalog;",
    )

    run_dbt_against_dev = BashOperator(
        task_id="run_dbt_against_dev",
        bash_command=f"{DBT} run --select dim_product_rated --target dev",
    )

    clone_point_in_time = SnowflakeOperator(
        task_id="clone_point_in_time",
        snowflake_conn_id="snowflake_conn",
        sql="""
        CREATE OR REPLACE DATABASE product_catalog_pit
        CLONE product_catalog AT(OFFSET => -60 * 5);
        """,
    )

    create_prototype_schema = SnowflakeOperator(
        task_id="create_prototype_schema",
        snowflake_conn_id="snowflake_conn",
        sql="""
        CREATE OR REPLACE SCHEMA product_catalog.prototype
        CLONE product_catalog.analytics;
        """,
    )

    run_prototype_dbt = BashOperator(
        task_id="run_prototype_dbt",
        bash_command=f"{DBT} run --select dim_product_rated --target prototype",
    )

    drop_prototype_schema = SnowflakeOperator(
        task_id="drop_prototype_schema",
        snowflake_conn_id="snowflake_conn",
        sql="DROP SCHEMA IF EXISTS product_catalog.prototype CASCADE;",
    )

    manage_backups = SnowflakeOperator(
        task_id="manage_backups",
        snowflake_conn_id="snowflake_conn",
        sql="""
        CREATE OR REPLACE DATABASE product_catalog_backup_{{ ds_nodash }}
        CLONE product_catalog;
        -- Seed then drop a 7-day-old name so the retention branch is visible in one demo
        CREATE OR REPLACE DATABASE product_catalog_backup_{{ macros.ds_add(ds, -7) | replace('-', '') }}
        CLONE product_catalog;
        DROP DATABASE IF EXISTS product_catalog_backup_{{ macros.ds_add(ds, -7) | replace('-', '') }};
        """,
    )

    restore_latest_backup = SnowflakeOperator(
        task_id="restore_latest_backup",
        snowflake_conn_id="snowflake_conn",
        sql="""
        CREATE OR REPLACE DATABASE product_catalog_restored
        CLONE product_catalog_backup_{{ ds_nodash }};
        SELECT COUNT(*) AS restored_rows
        FROM product_catalog_restored.analytics.dim_product;
        """,
    )

    clone_dev_database >> run_dbt_against_dev
    create_prototype_schema >> run_prototype_dbt >> drop_prototype_schema
    manage_backups >> restore_latest_backup

    # Independent branches after a logical "start"
    clone_dev_database >> clone_point_in_time
    clone_dev_database >> create_prototype_schema
    clone_dev_database >> manage_backups
