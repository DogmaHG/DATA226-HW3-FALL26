-- HW 3.2 — Snowflake objects for the product catalog pipeline
CREATE DATABASE IF NOT EXISTS product_catalog;
CREATE SCHEMA IF NOT EXISTS product_catalog.raw;
CREATE SCHEMA IF NOT EXISTS product_catalog.analytics;
CREATE SCHEMA IF NOT EXISTS product_catalog.snapshots;

CREATE OR REPLACE FILE FORMAT product_catalog.raw.product_csv
  TYPE = CSV
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  NULL_IF = ('', 'NULL');

CREATE OR REPLACE STAGE product_catalog.raw.product_stage
  FILE_FORMAT = product_catalog.raw.product_csv;

CREATE OR REPLACE TABLE product_catalog.raw.products (
  product_id    STRING,
  name          STRING,
  category      STRING,
  price         STRING,
  description   STRING,
  updated_at    TIMESTAMP_NTZ,
  _loaded_at    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  _filename     STRING
);

SHOW PARAMETERS LIKE 'DATA_RETENTION_TIME_IN_DAYS' IN ACCOUNT;
