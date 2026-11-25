"""Snowflake connection helpers. Reads credentials from env / `.env`."""
from __future__ import annotations

import os
from pathlib import Path

import snowflake.connector

ROOT = Path(__file__).resolve().parents[1]


def load_dotenv(path: Path | None = None) -> None:
    env_path = path or (ROOT / ".env")
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def connect(**overrides):
    load_dotenv()
    required = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise SystemExit(
            "Missing Snowflake credentials: "
            + ", ".join(missing)
            + f". Create {ROOT / '.env'} from .env.example."
        )
    # PAT is passed as password with default authenticator (Snowflake docs).
    authenticator = os.environ.get("SNOWFLAKE_AUTHENTICATOR", "snowflake")
    params = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "role": os.environ.get("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        "database": os.environ.get("SNOWFLAKE_DATABASE", "product_catalog"),
    }
    auth_l = authenticator.lower()
    if auth_l not in ("externalbrowser",):
        password = os.environ.get("SNOWFLAKE_PASSWORD")
        if not password:
            raise SystemExit(
                "SNOWFLAKE_PASSWORD is required (account password or PAT)."
            )
        params["password"] = password
    if auth_l == "programmatic_access_token":
        params["authenticator"] = "PROGRAMMATIC_ACCESS_TOKEN"
    elif auth_l == "externalbrowser":
        params["authenticator"] = "externalbrowser"
    # else: default snowflake authenticator; PAT works as password
    params.update(overrides)
    if params.get("database") is None:
        params.pop("database", None)
    return snowflake.connector.connect(**params)


def run_sql(sql: str, fetch: bool = False):
    conn = connect()
    try:
        cur = conn.cursor()
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        results = []
        for stmt in statements:
            cur.execute(stmt)
            if fetch:
                cols = [c[0] for c in cur.description] if cur.description else []
                rows = cur.fetchall() if cur.description else []
                results.append((cols, rows))
        return results
    finally:
        conn.close()
