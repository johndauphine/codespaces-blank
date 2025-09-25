#!/usr/bin/env python3
"""Deprecated wrapper script.

This file remains for backward compatibility. Prefer using the installed
console script `customer-gen` or importing from `customer_data_generator`.
"""

from customer_data_generator.cli import main

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

