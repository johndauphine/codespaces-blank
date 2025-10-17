import argparse
import os
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

from contextlib import contextmanager


try:
    import psycopg
    from psycopg.rows import dict_row
except Exception as e:  # pragma: no cover - handled at runtime
    psycopg = None  # type: ignore
    dict_row = None  # type: ignore


@dataclass
class DSN:
    dsn: str


def env_default(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.environ.get(name)
    return val if val else default


def build_dsn(
    *,
    host: Optional[str],
    port: Optional[str],
    user: Optional[str],
    password: Optional[str],
    dbname: Optional[str],
) -> str:
    parts: List[str] = []
    if host:
        parts.append(f"host={host}")
    if port:
        parts.append(f"port={port}")
    if user:
        parts.append(f"user={user}")
    if password:
        parts.append(f"password={password}")
    if dbname:
        parts.append(f"dbname={dbname}")
    return " ".join(parts)


@contextmanager
def pg_connect(dsn: str, autocommit: bool = False):
    if psycopg is None:
        raise RuntimeError(
            "psycopg is not installed. Please add 'psycopg[binary]~=3.2' to requirements."
        )
    conn = psycopg.connect(dsn, autocommit=autocommit)
    try:
        yield conn
    finally:
        conn.close()


def parse_table_list(include: Optional[str], exclude: Optional[str]) -> Tuple[Optional[Sequence[str]], Optional[Sequence[str]]]:
    inc = [t.strip() for t in include.split(",") if t.strip()] if include else None
    exc = [t.strip() for t in exclude.split(",") if t.strip()] if exclude else None
    return inc, exc


def list_tables(conn) -> List[Tuple[str, str]]:
    # returns list of (schema, table)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type='BASE TABLE' AND table_schema NOT IN ('pg_catalog','information_schema')
            ORDER BY table_schema, table_name
            """
        )
        rows = cur.fetchall()
        return [(r["table_schema"], r["table_name"]) for r in rows]


def matches(name: str, patterns: Sequence[str]) -> bool:
    # simple exact or schema.table matches; could be extended with fnmatch
    return name in patterns


def table_exists(conn, schema: str, table: str) -> bool:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema=%s AND table_name=%s AND table_type='BASE TABLE'
            """,
            (schema, table),
        )
        return cur.fetchone() is not None


def get_columns(src_conn, schema: str, table: str) -> List[Tuple[str, str, bool]]:
    # Returns list of (name, type_sql, not_null)
    with src_conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.attname AS name,
                   pg_catalog.format_type(a.atttypid, a.atttypmod) AS type_sql,
                   a.attnotnull AS not_null
            FROM pg_attribute a
            JOIN pg_class c ON a.attrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE c.relkind='r'
              AND n.nspname=%s
              AND c.relname=%s
              AND a.attnum > 0
              AND NOT a.attisdropped
            ORDER BY a.attnum
            """,
            (schema, table),
        )
        return [(name, type_sql, not_null) for name, type_sql, not_null in cur.fetchall()]


def get_primary_key(src_conn, schema: str, table: str) -> List[str]:
    with src_conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.attname
            FROM pg_index i
            JOIN pg_class c ON c.oid = i.indrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN LATERAL unnest(i.indkey) WITH ORDINALITY AS u(attnum, ord) ON TRUE
            JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = u.attnum
            WHERE i.indisprimary AND n.nspname = %s AND c.relname = %s
            ORDER BY u.ord
            """,
            (schema, table),
        )
        rows = cur.fetchall()
        return [r[0] for r in rows]


def ensure_table(dst_conn, src_conn, schema: str, table: str):
    # Create destination schema/table if missing based on source definition (columns + PK). Defaults, indexes, FKs are not copied.
    with dst_conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS \"{schema}\"")
    if not table_exists(dst_conn, schema, table):
        cols = get_columns(src_conn, schema, table)
        pk_cols = get_primary_key(src_conn, schema, table)
        if not cols:
            raise ValueError(f"Source table not found or has no columns: {schema}.{table}")
        col_defs = []
        for name, type_sql, not_null in cols:
            col_sql = f'"{name}" {type_sql}'
            if not_null:
                col_sql += " NOT NULL"
            col_defs.append(col_sql)
        if pk_cols:
            pk = ", ".join([f'"{c}"' for c in pk_cols])
            col_defs.append(f"PRIMARY KEY ({pk})")
        ddl = f'CREATE TABLE "{schema}"."{table}" (\n  ' + ",\n  ".join(col_defs) + "\n)";
        with dst_conn.cursor() as cur:
            cur.execute(ddl)


def copy_table(src_conn, dst_conn, schema: str, table: str, truncate: bool, create: bool, batch_size: int = 50000):
    fq = f'"{schema}"."{table}"'
    with src_conn.cursor() as s_cur, dst_conn.cursor() as d_cur:
        if create:
            ensure_table(dst_conn, src_conn, schema, table)
        if truncate:
            d_cur.execute(f"TRUNCATE TABLE {fq}")

        # Use COPY for fast transfer
        # Ensure schema search path contains the schema
        with s_cur.copy(f"COPY {fq} TO STDOUT WITH (FORMAT binary)") as copy_out:
            with d_cur.copy(f"COPY {fq} FROM STDIN WITH (FORMAT binary)") as copy_in:
                for data in copy_out:
                    copy_in.write(data)


def run_copy(
    src_dsn: str,
    dst_dsn: str,
    include: Optional[Sequence[str]] = None,
    exclude: Optional[Sequence[str]] = None,
    truncate: bool = False,
    create: bool = True,
) -> List[str]:
    copied: List[str] = []
    with pg_connect(src_dsn) as s_conn, pg_connect(dst_dsn) as d_conn:
        tables = list_tables(s_conn)
        for schema, table in tables:
            fq = f"{schema}.{table}"
            if include and not matches(fq, include):
                continue
            if exclude and matches(fq, exclude):
                continue
            copy_table(s_conn, d_conn, schema, table, truncate=truncate, create=create)
            copied.append(fq)
        d_conn.commit()
    return copied


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Copy PostgreSQL tables from one DB to another")
    # Source DSN args
    p.add_argument("--src-host", default=env_default("SRC_PGHOST"))
    p.add_argument("--src-port", default=env_default("SRC_PGPORT", "5432"))
    p.add_argument("--src-user", default=env_default("SRC_PGUSER"))
    p.add_argument("--src-password", default=env_default("SRC_PGPASSWORD"))
    p.add_argument("--src-db", default=env_default("SRC_PGDATABASE"))

    # Dest DSN args
    p.add_argument("--dst-host", default=env_default("DST_PGHOST"))
    p.add_argument("--dst-port", default=env_default("DST_PGPORT", "5432"))
    p.add_argument("--dst-user", default=env_default("DST_PGUSER"))
    p.add_argument("--dst-password", default=env_default("DST_PGPASSWORD"))
    p.add_argument("--dst-db", default=env_default("DST_PGDATABASE"))

    p.add_argument("--include", help="Comma-separated list of schema.table names to copy", default=None)
    p.add_argument("--exclude", help="Comma-separated list of schema.table names to skip", default=None)
    p.add_argument("--no-create", action="store_true", help="Do not create destination tables if missing")
    p.add_argument("--truncate", action="store_true", help="Truncate destination tables before copy")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    src_dsn = build_dsn(
        host=args.src_host, port=args.src_port, user=args.src_user, password=args.src_password, dbname=args.src_db
    )
    dst_dsn = build_dsn(
        host=args.dst_host, port=args.dst_port, user=args.dst_user, password=args.dst_password, dbname=args.dst_db
    )

    include, exclude = parse_table_list(args.include, args.exclude)
    try:
        copied = run_copy(src_dsn, dst_dsn, include=include, exclude=exclude, truncate=args.truncate, create=not args.no_create)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    if copied:
        print("Copied tables:")
        for name in copied:
            print(f" - {name}")
    else:
        print("No tables matched the criteria.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
