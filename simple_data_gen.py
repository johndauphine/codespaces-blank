#!/usr/bin/env python3
"""Minimal one-file script to generate synthetic customers or patients.

No-arg default (generates 100 customers to customers.csv):
    python simple_data_gen.py

Usage examples:
    python simple_data_gen.py customers 100 customers.csv --seed 42
    python simple_data_gen.py patients 50 patients.csv
    python simple_data_gen.py both 250 out_dir --seed 7

Modes (positional, all optional now with defaults):
    mode   -> customers | patients | both (default: customers)
    count  -> integer record count (default: 100)
    output -> output file (customers|patients) or directory for both (default: customers.csv)

If 'both' is selected, two files will be created inside the specified directory:
    customers.csv and patients.csv (or use --prefix to change base names)

Optional flags:
    --seed <int>     Deterministic output (stable IDs)
    --locale <code>  Faker locale (default en_US)
    --prefix <name>  When mode=both, base filename prefix (default '')

This is intentionally concise; for full CLI capabilities see generate_data.py.
"""
from __future__ import annotations

import sys
import argparse
from pathlib import Path

# Ensure local src/ on sys.path so we can import without installation.
# Resolve at runtime but also support execution from a copied temp directory
# where a sibling src/ might exist.
def _script_dir() -> Path:
    # Prefer __file__ but fall back to sys.argv[0] (which may be relative inside temp copy)
    try:
        return Path(__file__).resolve().parent
    except Exception:
        return Path(sys.argv[0]).resolve().parent if sys.argv and sys.argv[0] else Path.cwd()

SCRIPT_DIR = _script_dir()
candidate_src_dirs = [SCRIPT_DIR / "src", Path.cwd() / "src"]
for _src in candidate_src_dirs:
    if _src.exists() and str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

try:
    from customer_data_generator import (
        generate_customers_csv,
        generate_patients_csv,
    )
except Exception as e:  # pragma: no cover
    print(f"Import error: {e}", file=sys.stderr)
    print("Make sure the 'src' directory exists or install the package.", file=sys.stderr)
    sys.exit(1)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Minimal synthetic data generator (customers / patients / both)")
    p.add_argument("mode", nargs="?", default="customers", choices=["customers", "patients", "both"], help="What to generate (default: customers)")
    p.add_argument("count", nargs="?", type=int, default=100, help="Number of records for each entity (default: 100)")
    p.add_argument("output", nargs="?", default="customers.csv", help="Output file or directory when mode=both (default: customers.csv)")
    p.add_argument("--seed", type=int, default=None, help="Deterministic seed")
    p.add_argument("--locale", default="en_US", help="Faker locale (default en_US)")
    p.add_argument("--prefix", default="", help="Filename prefix when mode=both (default none)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.count < 0:
        print("Error: count must be >= 0", file=sys.stderr)
        return 2

    # Normalize output path for single-entity modes to current working directory
    if args.mode == "customers":
        out_path = Path(args.output)
        if not out_path.is_absolute():
            out_path = Path.cwd() / out_path
        path = generate_customers_csv(args.count, out_path, seed=args.seed, locale=args.locale)
        print(f"Wrote {args.count} customer records -> {path}")
        return 0
    if args.mode == "patients":
        out_path = Path(args.output)
        if not out_path.is_absolute():
            out_path = Path.cwd() / out_path
        path = generate_patients_csv(args.count, out_path, seed=args.seed, locale=args.locale)
        print(f"Wrote {args.count} patient records -> {path}")
        return 0

    # both
    out_dir = Path(args.output)
    if not out_dir.is_absolute():
        out_dir = Path.cwd() / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    cust_name = f"{args.prefix}customers.csv" if args.prefix else "customers.csv"
    pat_name = f"{args.prefix}patients.csv" if args.prefix else "patients.csv"
    cust_path = out_dir / cust_name
    pat_path = out_dir / pat_name
    generate_customers_csv(args.count, cust_path, seed=args.seed, locale=args.locale)
    generate_patients_csv(args.count, pat_path, seed=args.seed, locale=args.locale)
    print(f"Wrote {args.count} customer records -> {cust_path}")
    print(f"Wrote {args.count} patient records  -> {pat_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
