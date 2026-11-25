-- Zero-copy cloning demos (run after dim_product exists)

-- 9.1 Dev environment
CREATE OR REPLACE DATABASE dev_product_catalog CLONE product_catalog;

-- 9.2 Point-in-time (10 minutes ago; must be inside Time Travel retention)
CREATE OR REPLACE DATABASE product_catalog_pit
CLONE product_catalog AT(OFFSET => -60 * 10);

-- Compare a mutated product live vs PIT (adjust id if needed)
SELECT 'live' AS src, product_id, price, category, valid_from, valid_to, is_current
FROM product_catalog.analytics.dim_product
WHERE product_id = 'HD-00001'
UNION ALL
SELECT 'pit', product_id, price, category, valid_from, valid_to, is_current
FROM product_catalog_pit.analytics.dim_product
WHERE product_id = 'HD-00001'
ORDER BY src, valid_from;

-- 9.3 Rapid prototyping
CREATE OR REPLACE SCHEMA product_catalog.prototype CLONE product_catalog.analytics;
-- (run dbt --select dim_product_rated --target prototype, then query, then:)
-- DROP SCHEMA IF EXISTS product_catalog.prototype CASCADE;

-- 9.4 Backup + restore
CREATE OR REPLACE DATABASE product_catalog_backup_DEMO
CLONE product_catalog;

-- Seed a fake 7-day-old backup name so the drop branch is visible
CREATE OR REPLACE DATABASE product_catalog_backup_OLD7
CLONE product_catalog;
DROP DATABASE IF EXISTS product_catalog_backup_OLD7;

CREATE OR REPLACE DATABASE product_catalog_restored
CLONE product_catalog_backup_DEMO;

SELECT 'prod' AS db, COUNT(*) AS n FROM product_catalog.analytics.dim_product
UNION ALL
SELECT 'restored', COUNT(*) FROM product_catalog_restored.analytics.dim_product;

SHOW DATABASES LIKE 'product_catalog%';
SHOW DATABASES LIKE 'dev_product_catalog';
