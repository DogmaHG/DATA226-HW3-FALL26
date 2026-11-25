#!/usr/bin/env python3
"""Run acceptance queries and write report/evidence/scd_acceptance.txt."""
from __future__ import annotations

from pathlib import Path

from sf_connect import ROOT, connect, load_dotenv


def main() -> None:
    load_dotenv()
    out = ROOT / "report" / "evidence"
    out.mkdir(parents=True, exist_ok=True)
    sql = (ROOT / "sql" / "02_acceptance.sql").read_text()
    conn = connect()
    cur = conn.cursor()
    lines = []
    for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
        lines.append(f"\n-- {stmt.splitlines()[0][:100]}")
        cur.execute(stmt)
        cols = [c[0] for c in cur.description] if cur.description else []
        rows = cur.fetchall() if cur.description else []
        if cols:
            lines.append("\t".join(cols))
        for row in rows:
            lines.append("\t".join("" if v is None else str(v) for v in row))
        lines.append(f"({len(rows)} rows)")
    path = out / "scd_acceptance.txt"
    path.write_text("\n".join(lines) + "\n")
    print(path.read_text())
    print(f"wrote {path}")
    conn.close()


if __name__ == "__main__":
    main()
