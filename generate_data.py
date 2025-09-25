#!/usr/bin/env python3
"""Unified data generation wrapper (no install required).

Examples:
  python generate_data.py customers --count 500 --output customers.csv --seed 42
  python generate_data.py patients  --count 250 --output patients.csv  --seed 7

This script prepends the local `src` directory to PYTHONPATH so the package
can be imported directly after cloning without `pip install .`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    root = Path(__file__).resolve().parent
    src = root / "src"
    if src.exists():
        sys.path.insert(0, str(src))


_ensure_src_on_path()

try:
    from customer_data_generator import (
        generate_customers_csv,
        generate_patients_csv,
    )
except ImportError as e:  # pragma: no cover
    print("Import error:", e, file=sys.stderr)
    print("Ensure 'src' directory exists or install the package.", file=sys.stderr)
    sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate synthetic customers or patients (no install needed)."
    )
    sub = parser.add_subparsers(dest="entity", required=True, metavar="{customers,patients}")

    def add_common(p: argparse.ArgumentParser, default_output: str):
        p.add_argument("--count", "-c", type=int, required=True, help="Number of records to generate")
        p.add_argument("--output", "-o", default=default_output, help=f"Output CSV path (default: {default_output})")
        p.add_argument("--seed", type=int, default=None, help="Optional random seed (stabilizes IDs)")
        p.add_argument("--locale", default="en_US", help="Faker locale (default: en_US)")

    cust = sub.add_parser("customers", help="Generate synthetic customer data")
    add_common(cust, "customers.csv")

    pat = sub.add_parser("patients", help="Generate synthetic patient data (non-PHI demo)")
    add_common(pat, "patients.csv")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.entity == "customers":
        path = generate_customers_csv(
            count=args.count,
            path=args.output,
            seed=args.seed,
            locale=args.locale,
        )
        print(f"Wrote {args.count} customer records to {path}")
        return 0
    elif args.entity == "patients":
        path = generate_patients_csv(
            count=args.count,
            path=args.output,
            seed=args.seed,
            locale=args.locale,
        )
        print(f"Wrote {args.count} patient records to {path}")
        return 0
    else:  # pragma: no cover
        parser.error("Unknown entity type")
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
