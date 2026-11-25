#!/usr/bin/env python3
"""Create Snowflake database objects from sql/01_setup.sql."""
from __future__ import annotations

from pathlib import Path

from sf_connect import ROOT, connect, load_dotenv


def main() -> None:
    load_dotenv()
    sql_path = ROOT / "sql" / "01_setup.sql"
    sql = sql_path.read_text()
    conn = connect(database=None)
    cur = conn.cursor()
    for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
        print(f">> {stmt.splitlines()[0][:80]}")
        cur.execute(stmt)
        if cur.description:
            rows = cur.fetchall()
            for row in rows:
                print(row)
    print("Setup complete.")
    conn.close()


if __name__ == "__main__":
    main()
