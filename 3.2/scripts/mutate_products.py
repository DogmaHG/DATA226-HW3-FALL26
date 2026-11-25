#!/usr/bin/env python3
"""Change ~25 products for the SCD Type 2 proof (bumps updated_at only for those)."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from sf_connect import ROOT

N_CHANGE = 25


def main() -> None:
    src = ROOT / "data" / "products.csv"
    rows = list(csv.DictReader(src.open()))
    now = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")
    changed_ids = []
    for i, row in enumerate(rows):
        if i >= N_CHANGE:
            break
        old_price = float(row["price"])
        row["price"] = f"{round(old_price * 1.10, 2):.2f}"
        row["category"] = f"{row['category']} Sale"
        row["updated_at"] = now
        changed_ids.append(row["product_id"])

    fieldnames = ["product_id", "name", "category", "price", "description", "updated_at"]
    with src.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    manifest = ROOT / "data" / "mutated_ids.txt"
    manifest.write_text("\n".join(changed_ids) + "\n")
    print(f"mutated {len(changed_ids)} products; updated_at={now}")
    print(f"ids written to {manifest}")


if __name__ == "__main__":
    main()
