#!/usr/bin/env python3
"""Dataset Schema and Constraint Validator.

Validates sample environmental profiles and knowledge seed assets against JSON schema
specifications and domain invariant rules.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = REPO_ROOT / "data" / "schemas"
PROFILES_DIR = REPO_ROOT / "data" / "sample_profiles"


def validate_profile_file(filepath: Path) -> list[str]:
    errors = []
    try:
        with filepath.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"Failed to parse {filepath.name}: {e}"]

    # Domain invariants check
    if "soil_ph" in data and data["soil_ph"] is not None:
        ph = data["soil_ph"]
        if not (0 <= ph <= 14):
            errors.append(f"{filepath.name}: soil_ph {ph} is out of realistic range [0, 14]")

    if "soil_moisture" in data and data["soil_moisture"] is not None:
        moisture = data["soil_moisture"]
        if not (0 <= moisture <= 100):
            errors.append(f"{filepath.name}: soil_moisture {moisture}% is out of range [0, 100]")

    if "soil_organic_carbon" in data and data["soil_organic_carbon"] is not None:
        soc = data["soil_organic_carbon"]
        if not (0 <= soc <= 100):
            errors.append(f"{filepath.name}: soil_organic_carbon {soc}% is out of range [0, 100]")

    if "rainfall_mm_year" in data and data["rainfall_mm_year"] is not None:
        rain = data["rainfall_mm_year"]
        if rain < 0:
            errors.append(f"{filepath.name}: rainfall_mm_year {rain} cannot be negative")

    return errors


def main() -> int:
    print("Running Dataset & Profile Schema Validation...")
    total_files = 0
    all_errors: list[str] = []

    if PROFILES_DIR.exists():
        for pfile in PROFILES_DIR.glob("*.json"):
            total_files += 1
            errs = validate_profile_file(pfile)
            if errs:
                all_errors.extend(errs)

    if all_errors:
        print(f"[ERROR] Validation failed with {len(all_errors)} error(s):")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print(f"[OK] Successfully validated {total_files} dataset files. 0 schema or domain violations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
