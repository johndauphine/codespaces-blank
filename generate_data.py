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
import subprocess
import importlib
from pathlib import Path


def _ensure_src_on_path() -> None:
    root = Path(__file__).resolve().parent
    src = root / "src"
    if src.exists():
        sys.path.insert(0, str(src))


_ensure_src_on_path()


def _bootstrap_dependencies() -> None:
    """Attempt to ensure required runtime dependency (faker) is available.

    This avoids forcing the user to install pip first in very minimal Python environments.
    If installation fails, we surface a friendly message and exit.
    """
    try:
        importlib.import_module("faker")
        return  # already present
    except ImportError:
        pass

    print("Dependency 'faker' not found. Attempting lightweight installation...", file=sys.stderr)
    # Try ensurepip (may be unavailable in some distros if removed by vendor)
    try:
        import ensurepip  # type: ignore
        ensurepip.bootstrap()
    except Exception as e:  # pragma: no cover
        print(f"Warning: ensurepip failed or unavailable ({e}). Continuing to try pip anyway.", file=sys.stderr)

    python_exec = sys.executable
    try:
        subprocess.check_call([python_exec, "-m", "pip", "install", "faker>=25.0.0,<26.0.0"], stdout=subprocess.DEVNULL)
    except Exception as e:  # pragma: no cover
        print("Automatic install failed.", file=sys.stderr)
        print("Please install dependencies manually, e.g.:", file=sys.stderr)
        print("  python -m ensurepip --upgrade  # if pip missing", file=sys.stderr)
        print("  python -m pip install -r requirements.txt", file=sys.stderr)
        print(f"Underlying error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        importlib.import_module("faker")
    except ImportError:  # pragma: no cover
        print("Installation reported success but 'faker' still not importable.", file=sys.stderr)
        sys.exit(1)


_bootstrap_dependencies()

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
