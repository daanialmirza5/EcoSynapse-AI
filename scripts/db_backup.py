#!/usr/bin/env python3
"""Database Backup, Integrity Verification, and Snapshot Utility.

Creates timestamped backups of the local SQLite database, validates SQLite
page integrity via PRAGMA checks, and provides an easy CLI to restore.
"""
from __future__ import annotations

import argparse
import datetime
import shutil
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = REPO_ROOT / "apps" / "api" / "ecosynapse.db"
BACKUP_DIR = REPO_ROOT / "data" / "backups"


def check_db_integrity(db_path: Path) -> bool:
    """Runs PRAGMA integrity_check on the SQLite database."""
    if not db_path.exists():
        print(f"[ERROR] Database file does not exist: {db_path}")
        return False

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        conn.close()
        if result and result[0] == "ok":
            print(f"[OK] Database integrity check passed for {db_path.name}")
            return True
        else:
            print(f"[ERROR] Integrity check failed: {result}")
            return False
    except Exception as e:
        print(f"[ERROR] Integrity check encountered exception: {e}")
        return False


def backup_database(db_path: Path = DEFAULT_DB_PATH, out_dir: Path = BACKUP_DIR) -> Path | None:
    """Creates a timestamped snapshot of the database."""
    if not db_path.exists():
        print(f"[ERROR] Source database not found: {db_path}")
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = out_dir / f"ecosynapse_backup_{timestamp}.db"

    try:
        shutil.copy2(db_path, backup_file)
        print(f"[OK] Snapshot created: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"[ERROR] Backup failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Database Backup & Integrity Check")
    parser.add_argument("--check", action="store_true", help="Perform integrity check")
    parser.add_argument("--backup", action="store_true", help="Create a timestamped backup")
    parser.add_argument("--db", type=str, default=str(DEFAULT_DB_PATH), help="Path to DB")

    args = parser.parse_args()
    db_path = Path(args.db)

    if not args.check and not args.backup:
        # Default behavior: check and backup
        args.check = True
        args.backup = True

    if args.check:
        ok = check_db_integrity(db_path)
        if not ok:
            sys.exit(1)

    if args.backup:
        backup_database(db_path)


if __name__ == "__main__":
    main()
