# -*- coding: utf-8 -*-
"""
clean_old.py - Clean old test files and temporary artifacts.
Usage:
    python clean_old.py              # dry run (show what would be deleted)
    python clean_old.py --delete     # actually delete files
"""

import argparse
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

TEST_PATTERNS = [
    "test_*.xlsx",
    "test_*.html",
    "test_*.log",
    "github_check*.xlsx",
    "rebuild_*.xlsx",
    "enc_pat.py",
    "fix_wf*.py",
]

TEST_DIRS = [
    ROOT_DIR / "run" / "__pycache__",
    ROOT_DIR / "run" / "logs",
    ROOT_DIR / "run" / "archive",
]


def find_files() -> list[Path]:
    found = []
    for pattern in TEST_PATTERNS:
        found.extend(ROOT_DIR.glob(pattern))
    for d in TEST_DIRS:
        if d.exists():
            found.append(d)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean old test files")
    parser.add_argument("--delete", action="store_true", help="Actually delete files")
    args = parser.parse_args()

    files = find_files()
    if not files:
        print("Nothing to clean.")
        return 0

    print(f"Found {len(files)} items to clean:")
    for f in files:
        size = f.stat().st_size if f.is_file() else 0
        print(f"  {'[DIR] ' if f.is_dir() else '      '}{f.name} ({size} bytes)")

    if not args.delete:
        print("\nDry run. Use --delete to actually remove files.")
        return 0

    for f in files:
        try:
            if f.is_dir():
                shutil.rmtree(str(f))
            else:
                f.unlink()
            print(f"  Deleted: {f.name}")
        except Exception as e:
            print(f"  Error deleting {f.name}: {e}")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
