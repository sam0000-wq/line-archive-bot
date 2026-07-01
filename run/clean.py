# -*- coding: utf-8 -*-
"""
clean.py - Clean up local development artifacts.
Usage:
    python clean.py          # remove artifacts, keep .env
    python clean.py --all    # also remove .env and venv
    python clean.py --dry    # dry run
"""

import argparse
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _size_str(path: Path) -> str:
    if path.is_file():
        size = path.stat().st_size
    elif path.is_dir():
        size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    else:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def _remove(target: Path, dry_run: bool) -> bool:
    if not target.exists():
        return False
    size = _size_str(target)
    if dry_run:
        print(f"  [DRY-RUN] Would remove: {target.relative_to(BASE_DIR)} ({size})")
        return True
    if target.is_dir():
        shutil.rmtree(target, ignore_errors=True)
    else:
        target.unlink(missing_ok=True)
    print(f"  [OK] Removed: {target.relative_to(BASE_DIR)} ({size})")
    return True


def clean(dry_run: bool = False, remove_all: bool = False) -> int:
    targets: list[Path] = [
        BASE_DIR / "__pycache__",
        BASE_DIR / "archive",
        BASE_DIR / "logs",
        BASE_DIR / "deploy_report.html",
        BASE_DIR / "test_report.html",
        BASE_DIR / "test_report.json",
    ]
    for pycache in BASE_DIR.rglob("__pycache__"):
        if pycache.is_dir():
            targets.append(pycache)
    if remove_all:
        targets.append(BASE_DIR / "venv")
        targets.append(BASE_DIR / ".env")
    removed = 0
    skipped = 0
    for t in targets:
        if _remove(t, dry_run):
            removed += 1
        else:
            skipped += 1
    print(f"\nCleanup complete: {removed} removed, {skipped} not found.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean up LINE Archive Bot artifacts")
    parser.add_argument("--all", action="store_true", help="Also remove .env and venv")
    parser.add_argument("--dry", action="store_true", help="Dry run")
    args = parser.parse_args()
    print("LINE Archive Bot - Cleanup Script")
    return clean(dry_run=args.dry, remove_all=args.all)


if __name__ == "__main__":
    sys.exit(main())
