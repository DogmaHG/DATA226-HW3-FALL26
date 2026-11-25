#!/usr/bin/env python3
"""Run extract → load → dbt build → verify (same order as product_catalog_etl)."""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from load_products import extract_check, load  # noqa: E402
from sf_connect import connect, load_dotenv  # noqa: E402


def main() -> None:
    load_dotenv()
    os.environ.setdefault("DBT_PROFILES_DIR", str(ROOT / "dbt" / "product_catalog"))
    evidence = ROOT / "report" / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    log_lines = [f"product_catalog_etl run @ {datetime.now(timezone.utc).isoformat()}"]

    def step(name: str, fn):
        log_lines.append(f"\n== {name} ==")
        print(f"== {name} ==")
        fn()
        log_lines.append(f"{name}: SUCCESS")

    step("extract_products", lambda: extract_check(ROOT / "data" / "products.csv"))
    step("load_products", lambda: load(ROOT / "data" / "products.csv"))

    def dbt_build():
        subprocess.check_call(
            [
                "dbt",
                "build",
                "--project-dir",
                str(ROOT / "dbt" / "product_catalog"),
                "--profiles-dir",
                os.environ["DBT_PROFILES_DIR"],
            ]
        )

    step("dbt_build", dbt_build)

    def verify():
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM product_catalog.raw.products")
        raw_n = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM product_catalog.analytics.dim_product")
        dim_n = cur.fetchone()[0]
        conn.close()
        log_lines.append(f"raw.products={raw_n} dim_product={dim_n}")
        if raw_n == 0 or dim_n == 0:
            raise RuntimeError("verify_row_counts failed: empty table")

    step("verify_row_counts", verify)

    path = evidence / "airflow_etl_run_log.txt"
    path.write_text("\n".join(log_lines) + "\n")
    # Also record task graph for the write-up
    (evidence / "airflow_etl_task_graph.txt").write_text(
        "extract_products >> load_products >> dbt_build >> verify_row_counts\n"
        "DAG id: product_catalog_etl\n"
        "schedule: @daily; retries=1\n"
        "Errors: missing/empty CSV fails extract; dbt fails on test errors; "
        "verify fails if raw or dim_product is empty.\n"
    )
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
