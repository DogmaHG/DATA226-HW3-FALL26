#!/usr/bin/env python3
"""Execute zero-copy clone demos and write evidence files."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sf_connect import ROOT, connect, load_dotenv


def q(cur, sql: str):
    print(f">> {sql.splitlines()[0][:100]}")
    cur.execute(sql)
    if cur.description:
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        return cols, rows
    return [], []


def dump(path: Path, title: str, cols, rows) -> None:
    lines = [title, "\t".join(cols)]
    for row in rows:
        lines.append("\t".join("" if v is None else str(v) for v in row))
    lines.append(f"({len(rows)} rows)\n")
    path.write_text("\n".join(lines))
    print(path)


def main() -> None:
    load_dotenv()
    evidence = ROOT / "report" / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    dbt_dir = ROOT / "dbt" / "product_catalog"
    import os

    profiles = Path(
        os.environ.get("DBT_PROFILES_DIR", str(dbt_dir))
    )
    env = dict(**{k: v for k, v in os.environ.items()})
    env.setdefault("DBT_PROFILES_DIR", str(profiles))

    conn = connect()
    cur = conn.cursor()

    # Retention parameter
    cols, rows = q(
        cur,
        "SHOW PARAMETERS LIKE 'DATA_RETENTION_TIME_IN_DAYS' IN ACCOUNT",
    )
    dump(evidence / "time_travel_retention.txt", "Account Time Travel retention", cols, rows)

    # 9.1 Dev clone
    q(cur, "CREATE OR REPLACE DATABASE dev_product_catalog CLONE product_catalog")
    subprocess.check_call(
        [
            "dbt",
            "run",
            "--select",
            "dim_product_rated",
            "--target",
            "dev",
            "--project-dir",
            str(dbt_dir),
            "--profiles-dir",
            str(profiles),
        ],
        cwd=str(dbt_dir),
        env=env,
    )
    cols, rows = q(
        cur,
        """
        SELECT product_id, name, product_rating, price_band
        FROM dev_product_catalog.analytics.dim_product_rated
        WHERE is_current
        LIMIT 10
        """,
    )
    dump(evidence / "clone_dev_rated.txt", "Dev clone + dim_product_rated sample", cols, rows)

    # 9.2 Point-in-time: after v1 dim_product, before SCD mutate snapshot.
    # Session TZ is America/Los_Angeles; trial Time Travel is ~1 day (not 2023).
    pit_ts = os.environ.get(
        "HW32_PIT_TIMESTAMP", "2026-11-25 10:51:45 -0800"
    )
    q(
        cur,
        "CREATE OR REPLACE DATABASE product_catalog_pit "
        f"CLONE product_catalog AT(TIMESTAMP => '{pit_ts}'::TIMESTAMP_TZ)",
    )
    (evidence / "clone_pit_timestamp.txt").write_text(
        f"PIT clone timestamp: {pit_ts}\n"
        "(after first successful dim_product build, before SCD mutate)\n"
    )
    cols, rows = q(
        cur,
        """
        SELECT 'live' AS src, product_id, price, category, valid_from, valid_to, is_current
        FROM product_catalog.analytics.dim_product
        WHERE product_id = 'HD-00001'
        UNION ALL
        SELECT 'pit', product_id, price, category, valid_from, valid_to, is_current
        FROM product_catalog_pit.analytics.dim_product
        WHERE product_id = 'HD-00001'
        ORDER BY 1, 5
        """,
    )
    dump(evidence / "clone_point_in_time.txt", "Live vs PIT for HD-00001", cols, rows)

    cols, rows = q(
        cur,
        """
        SELECT 'live_current' AS metric, COUNT(*) AS n
        FROM product_catalog.analytics.dim_product WHERE is_current
        UNION ALL
        SELECT 'pit_current', COUNT(*)
        FROM product_catalog_pit.analytics.dim_product WHERE is_current
        """,
    )
    dump(evidence / "clone_pit_analysis.txt", "Current product counts live vs PIT", cols, rows)

    # 9.3 Prototype schema
    q(
        cur,
        "CREATE OR REPLACE SCHEMA product_catalog.prototype CLONE product_catalog.analytics",
    )
    subprocess.check_call(
        [
            "dbt",
            "run",
            "--select",
            "dim_product_rated",
            "--target",
            "prototype",
            "--project-dir",
            str(dbt_dir),
            "--profiles-dir",
            str(profiles),
        ],
        cwd=str(dbt_dir),
        env=env,
    )
    cols, rows = q(
        cur,
        """
        SELECT product_id, price_band, product_rating
        FROM product_catalog.prototype.dim_product_rated
        LIMIT 10
        """,
    )
    dump(evidence / "clone_prototype.txt", "Prototype schema dim_product_rated", cols, rows)
    q(cur, "DROP SCHEMA IF EXISTS product_catalog.prototype CASCADE")

    # 9.4 Backup / restore
    today = datetime.utcnow().strftime("%Y%m%d")
    old = (datetime.utcnow() - timedelta(days=7)).strftime("%Y%m%d")
    q(
        cur,
        f"CREATE OR REPLACE DATABASE product_catalog_backup_{today} CLONE product_catalog",
    )
    q(
        cur,
        f"CREATE OR REPLACE DATABASE product_catalog_backup_{old} CLONE product_catalog",
    )
    q(cur, f"DROP DATABASE IF EXISTS product_catalog_backup_{old}")
    q(
        cur,
        f"CREATE OR REPLACE DATABASE product_catalog_restored "
        f"CLONE product_catalog_backup_{today}",
    )
    cols, rows = q(
        cur,
        """
        SELECT 'prod' AS db, COUNT(*) AS n FROM product_catalog.analytics.dim_product
        UNION ALL
        SELECT 'restored', COUNT(*) FROM product_catalog_restored.analytics.dim_product
        """,
    )
    dump(evidence / "clone_backup_restore.txt", "Backup restore row counts", cols, rows)

    cols, rows = q(cur, "SHOW DATABASES LIKE 'product_catalog%'")
    dump(evidence / "clone_databases.txt", "SHOW DATABASES LIKE product_catalog%", cols, rows)

    conn.close()
    print("Clone demos complete.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"dbt failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
