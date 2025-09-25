from __future__ import annotations

import argparse
import sys

from .generator import generate_customers_csv


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate fabricated customer data CSV")
    p.add_argument("--count", "-c", type=int, required=True, help="Number of customer records to generate")
    p.add_argument("--output", "-o", default="customers.csv", help="Output CSV file path (default: customers.csv)")
    p.add_argument("--seed", type=int, default=None, help="Optional random seed for reproducibility")
    p.add_argument("--locale", default="en_US", help="Faker locale (default: en_US)")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        path = generate_customers_csv(count=args.count, path=args.output, seed=args.seed, locale=args.locale)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    print(f"Wrote {args.count} records to {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
