#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from trusted_data_demo.compiler import write_python_sdk_packages


def main() -> None:
    written = write_python_sdk_packages(ROOT / "generated" / "python")
    for product_id, path in written.items():
        print(f"{product_id}: {path}")


if __name__ == "__main__":
    main()
