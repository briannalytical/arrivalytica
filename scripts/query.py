"""Run a .sql file against the bronze data lake with DuckDB.

Usage (from the project root):
    python3 scripts/query.py queries/route_summary.sql
"""

import sys
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/query.py <path/to/query.sql>", file=sys.stderr)
        return 1

    sql_path = Path(sys.argv[1])
    if not sql_path.is_absolute():
        sql_path = PROJECT_ROOT / sql_path
    if not sql_path.exists():
        print(f"No such file: {sql_path}", file=sys.stderr)
        return 1

    # Run relative to the project root so 'data/...' paths in queries
    # resolve no matter where the command was invoked from.
    con = duckdb.connect()
    con.execute(f"SET file_search_path = '{PROJECT_ROOT}'")
    result = con.sql(sql_path.read_text())
    if result is not None:
        result.show(max_rows=100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
