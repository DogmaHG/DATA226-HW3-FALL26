#!/usr/bin/env python3
"""PUT local products.csv to internal stage and COPY INTO RAW.PRODUCTS."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sf_connect import ROOT, connect, load_dotenv


def extract_check(csv_path: Path) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(f"Source file missing: {csv_path}")
    lines = csv_path.read_text().splitlines()
    if len(lines) < 2:
        raise ValueError(f"Source file empty or header-only: {csv_path}")
    print(f"extract ok: {csv_path} ({len(lines) - 1} data rows)")


def load(csv_path: Path) -> None:
    load_dotenv()
    extract_check(csv_path)
    conn = connect()
    cur = conn.cursor()
    abs_path = csv_path.resolve().as_posix().replace("'", "\\'")
    cur.execute("USE DATABASE product_catalog")
    cur.execute("USE SCHEMA raw")
    cur.execute("TRUNCATE TABLE IF EXISTS product_catalog.raw.products")
    # Quote path — homework folder name contains spaces ("HW 3/3.2")
    put_sql = (
        f"PUT 'file://{abs_path}' @product_catalog.raw.product_stage "
        "AUTO_COMPRESS=FALSE OVERWRITE=TRUE"
    )
    print(f">> {put_sql}")
    cur.execute(put_sql)
    copy_sql = """
    COPY INTO product_catalog.raw.products
      (product_id, name, category, price, description, updated_at)
    FROM @product_catalog.raw.product_stage
    FILE_FORMAT = (FORMAT_NAME = product_catalog.raw.product_csv)
    PATTERN = '.*products.*[.]csv'
    ON_ERROR = 'ABORT_STATEMENT'
    """
    print(">> COPY INTO product_catalog.raw.products ...")
    cur.execute(copy_sql)
    for row in cur.fetchall():
        print(row)
    cur.execute(
        """
        UPDATE product_catalog.raw.products
        SET _filename = 'products.csv',
            _loaded_at = CURRENT_TIMESTAMP()
        WHERE _filename IS NULL
        """
    )
    cur.execute("SELECT COUNT(*) FROM product_catalog.raw.products")
    print(f"raw.products rows: {cur.fetchone()[0]}")
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / "data" / "products.csv",
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="Validate the source file without loading",
    )
    args = parser.parse_args()
    if args.extract_only:
        extract_check(args.csv)
        return
    try:
        load(args.csv)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
