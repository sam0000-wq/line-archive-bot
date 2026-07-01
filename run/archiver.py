# -*- coding: utf-8 -*-
"""Message classification and xlsx archiving module."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from config import Config

logger = logging.getLogger(__name__)
COLUMNS = ["timestamp", "sender_name", "sender_user_id", "message"]
SHEET_CRITICAL = "critical"
SHEET_WARNING = "warning"
SHEET_OTHERS = "others"


def _daily_path(date: Optional[datetime] = None) -> Path:
    if date is None:
        date = datetime.now()
    filename = f"line_archive_{date.strftime('%Y%m%d')}.xlsx"
    Config.ensure_dirs()
    return Config.ARCHIVE_DIR / filename


def _get_sheet_name(text: str) -> str:
    cleaned = text.lower().strip()
    if cleaned.startswith("critical:"):
        return SHEET_CRITICAL
    if cleaned.startswith("warning:"):
        return SHEET_WARNING
    return SHEET_OTHERS


def _ensure_workbook(path: Path) -> Workbook:
    if path.exists():
        return load_workbook(str(path))
    wb = Workbook()
    default_ws = wb.active
    wb.remove(default_ws)
    bold = Font(bold=True)
    for sheet_name in (SHEET_CRITICAL, SHEET_WARNING, SHEET_OTHERS):
        ws = wb.create_sheet(title=sheet_name)
        ws.append(COLUMNS)
        for col_idx in range(1, len(COLUMNS) + 1):
            ws.cell(row=1, column=col_idx).font = bold
    wb.save(str(path))
    return load_workbook(str(path))


def archive_message(timestamp: str, sender_name: str, sender_user_id: str, message: str) -> str:
    sheet_name = _get_sheet_name(message)
    path = _daily_path()
    try:
        wb = _ensure_workbook(path)
        ws = wb[sheet_name]
        ws.append([timestamp, sender_name, sender_user_id, message])
        wb.save(str(path))
        logger.info("Archived to [%s] %s: %s", sheet_name, path.name, message[:60])
        return sheet_name
    except Exception:
        logger.exception("Failed to archive message to %s", path)
        raise


def get_archive_path(date_str: Optional[str] = None) -> Optional[Path]:
    if date_str:
        path = Config.ARCHIVE_DIR / f"line_archive_{date_str}.xlsx"
    else:
        path = _daily_path()
    return path if path.exists() else None
