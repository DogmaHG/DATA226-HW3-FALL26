# HW 3.2 — E-commerce Product Catalog

Part 2 of 4. **25 points** across **11 deliverables**.

Build a pipeline that ingests a product catalog, loads it into Snowflake, transforms it with dbt, and keeps product history as a Slowly Changing Dimension (SCD) Type 2. Apache Airflow runs the pipeline.

The instructor’s snippets below are a starting point. The prompt says full credit depends on your own workflow and your own code.

## Mandatory questions

Points may be deducted if these are skipped.

1. Did you find or come across solutions to similar problems by using Generative AI or other sources?
2. If yes, give full details of the model (including the prompt used), website, or person. State the question number and the help they provided.

## What to build

```text
source file
    →  Airflow extract
    →  Airflow load into a Snowflake staging table
    →  dbt staging model
    →  dbt snapshot and a Type 2 product dimension
    →  dbt tests
    →  Snowflake checks, including a second run after the source changes
```

Separate from that daily path, use Snowflake zero-copy cloning for a dev database, a point-in-time copy, a prototype schema, and a short backup/restore cycle.

## Rubric

The bracketed points in the original prompt sum to 25. Grouped into the 11 deliverables named in the header:

| # | Deliverable | Points | What earns it |
|---|-------------|--------|----------------|
| 1 | Development environment | 1 | Python 3.8+, Airflow, dbt, a Snowflake account, `snowflake-connector-python` |
| 2 | Source dataset | 1 | A product catalog file in S3 or on the local filesystem |
| 3 | Snowflake setup | 1 | Database, schema, and a staging table for the raw file |
| 4 | Airflow DAG | 4 | Extract (1), load to staging (1), trigger dbt (1), error handling (1) |
| 5 | dbt models | 6 | Project (1), staging model (1), SCD Type 2 core model (2), tests (2) |
| 6 | dbt snapshot | 1 | A snapshot that tracks product history |
| 7 | dbt invoked from Airflow | 1 | The DAG runs the dbt project with a dbt operator or equivalent |
| 8 | End-to-end test | 3 | DAG run (1), rows visible in Snowflake (1), source change plus rerun proves SCD (1) |
| 9 | Zero-copy cloning | 4 | Dev clone (1), point-in-time clone (1), prototype schema (1), backup and restore (1) |
| 10 | Five takeaways | 2 | Short write-up of what you actually observed |
| 11 | Extension | 1 | How you would extend the exercise |

Deliverable 7 overlaps the “trigger dbt” point inside deliverable 4. One real dbt task can cover both lines if the write-up maps each rubric line to a task id.

Suggested dataset: [Home Depot products on Kaggle](https://www.kaggle.com/datasets/thedevastator/the-home-depot-products-dataset).

## Steps

### 1. Development environment (1 point)

- Install Python 3.8 or newer (Mac, Windows, or Linux).
- Install Apache Airflow.
- Install dbt: [dbt Core with pip](https://docs.getdbt.com/docs/core/pip-install).
- Set up a Snowflake account.
- Install the Snowflake connector: `pip install snowflake-connector-python`.

### 2. Source a dataset (1 point)

- Use a product catalog such as the Home Depot set linked above.
- Store the file in an S3 bucket or on the local filesystem.

### 3. Snowflake (1 point)

- Create a database and schema.
- Create a staging table that receives the raw file.

### 4. Airflow DAG (4 points)

Create a DAG file in the Airflow `dags` folder.

| Point | Task |
|-------|------|
| 1 | Extract from the source |
| 1 | Load into the Snowflake staging table |
| 1 | Trigger `dbt run` |
| 1 | Error handling |

Use Airflow operators that match those tasks.

### 5. dbt models (6 points)

| Point | Model |
|-------|--------|
| 1 | dbt project structure |
| 1 | Staging model that cleans and prepares the data |
| 2 | Core model that implements SCD Type 2 for the product dimension |
| 2 | Tests for the models |

### 6. dbt snapshot (1 point)

Implement a snapshot on the product dimension so historical changes are tracked.

### 7. dbt from Airflow (1 point)

Call dbt from the DAG (the prompt says “the `dbt` operator”; a Bash operator that runs the project meets the same requirement if you document it).

### 8. Test the pipeline (3 points)

- Run the DAG.
- Verify the data in Snowflake.
- Change the source data, rerun, and show that SCD Type 2 kept the old version and opened a new one.

### 9. Snowflake zero-copy cloning (4 points)

#### 9.1 Development environment (1 point)

Clone production so experiments do not touch production data.

```sql
CREATE DATABASE dev_product_catalog CLONE product_catalog;
```

The prompt also asks for:

- An Airflow task that creates this clone daily.
- A dbt model in the development environment that tries a new feature (for example, a product rating column).
- A DAG (or a clearly separated task group) that runs dbt against that development environment.
- A note on promoting the tested change into production after it succeeds.

```python
clone_dev_db = SnowflakeOperator(
    task_id="clone_dev_database",
    sql="""
    CREATE OR REPLACE DATABASE dev_product_catalog CLONE product_catalog;
    """,
    snowflake_conn_id="snowflake_conn",
    dag=dag,
)
```

#### 9.2 Point-in-time analysis (1 point)

Clone the catalog as of a specific timestamp, then run a dbt model that does year-over-year analysis against that clone. The prompt’s example:

```sql
CREATE DATABASE product_catalog_eoy_2023
CLONE product_catalog AT(TIMESTAMP => '2023-12-31 23:59:59'::timestamp_ntz);
```

And an Airflow task meant to run at year end:

```python
create_eoy_snapshot = SnowflakeOperator(
    task_id="create_eoy_snapshot",
    sql="""
    CREATE OR REPLACE DATABASE product_catalog_eoy_{{ execution_date.year }}
    CLONE product_catalog AT(TIMESTAMP => '{{ execution_date.year }}-12-31 23:59:59'::timestamp_ntz);
    """,
    snowflake_conn_id="snowflake_conn",
    dag=dag,
)
```

#### 9.3 Rapid prototyping (1 point)

Clone one schema, try a heavier transformation there, then remove the clone.

```sql
CREATE SCHEMA prototype_schema CLONE product_catalog.public;
```

```python
prototype_test = SnowflakeOperator(
    task_id="run_prototype",
    sql="""
    CREATE OR REPLACE SCHEMA prototype_schema CLONE product_catalog.public;

    USE SCHEMA prototype_schema;

    -- Run your prototype dbt model here

    DROP SCHEMA prototype_schema;
    """,
    snowflake_conn_id="snowflake_conn",
    dag=dag,
)
```

#### 9.4 Backup and restore (1 point)

Take a daily clone, keep seven days, and document a restore from the newest backup.

```sql
CREATE OR REPLACE DATABASE product_catalog_backup_{{ ds_nodash }}
CLONE product_catalog;
```

```python
manage_backups = SnowflakeOperator(
    task_id="manage_backups",
    sql="""
    -- Create today's backup
    CREATE DATABASE IF NOT EXISTS product_catalog_backup_{{ ds_nodash }}
    CLONE product_catalog;

    -- Drop backups older than 7 days
    DROP DATABASE IF EXISTS product_catalog_backup_{{ macros.ds_add(ds, -7) }};
    """,
    snowflake_conn_id="snowflake_conn",
    dag=dag,
)
```

### 10. Five takeaways (2 points)

Experiment with the options above and describe five things you learned.

### 11. Extension (1 point)

If you could change this exercise, how would you make the learning experience better?

## Instructor starter code

These are the snippets from the prompt, reformatted only for whitespace. Treat them as a sketch.

### Airflow DAG

```python
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.providers.amazon.aws.transfers.s3_to_snowflake import S3ToSnowflakeOperator
from airflow.operators.bash_operator import BashOperator

dag = DAG(
    "product_catalog_etl",
    default_args=default_args,
    description="ETL for Product Catalog",
    schedule_interval=timedelta(days=1),
)

extract_task = S3ToSnowflakeOperator(
    task_id="extract_from_s3",
    s3_keys=["product_data.csv"],
    table="raw_products",
    schema="staging",
    stage="my_s3_stage",
    file_format="my_csv_format",
    dag=dag,
)

dbt_run = BashOperator(
    task_id="dbt_run",
    bash_command="dbt run --profiles-dir /opt/airflow/dbt --project-dir /opt/airflow/dbt",
    dag=dag,
)

extract_task >> dbt_run
```

### SCD Type 2 model

```sql
{{ config(materialized='table') }}

WITH source_data AS (
    SELECT * FROM {{ ref('stg_products') }}
),
updates AS (
    SELECT
        *,
        LAG(updated_at) OVER (PARTITION BY id ORDER BY updated_at) AS prev_updated_at
    FROM source_data
),
scd_data AS (
    SELECT
        id,
        name,
        category,
        price,
        description,
        created_at,
        updated_at,
        CASE
            WHEN prev_updated_at IS NULL THEN updated_at
            ELSE prev_updated_at
        END AS valid_from,
        LEAD(updated_at) OVER (PARTITION BY id ORDER BY updated_at) AS valid_to
    FROM updates
)
SELECT
    {{ dbt_utils.surrogate_key(['id', 'valid_from']) }} AS surrogate_key,
    *,
    CASE WHEN valid_to IS NULL THEN TRUE ELSE FALSE END AS is_current
FROM scd_data
```

### Snapshot configuration

```yaml
# dbt_project.yml
snapshots:
  product_catalog:
    target_schema: snapshots
    strategy: timestamp
    updated_at: updated_at
    unique_key: id
```

```sql
-- snapshots/product_snapshot.sql
{% snapshot product_snapshot %}
    {{
        config(
          target_schema='snapshots',
          strategy='timestamp',
          unique_key='id',
          updated_at='updated_at',
        )
    }}
    SELECT * FROM {{ source('staging', 'products') }}
{% endsnapshot %}
```

## References

- [Apache Airflow](https://airflow.apache.org/docs/)
- [dbt](https://docs.getdbt.com/)
- [Snowflake](https://docs.snowflake.com/)
- [dbt with Snowflake](https://docs.getdbt.com/reference/warehouse-setups/snowflake-setup)
- [Airflow Snowflake provider](https://airflow.apache.org/docs/apache-airflow-providers-snowflake/stable/index.html)

Working plan, file layout, and the starter-code corrections: [execution-plan.md](execution-plan.md).
