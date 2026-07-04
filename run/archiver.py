# -*- coding: utf-8 -*-
"""Message classification and xlsx archiving module."""

import logging
import requests as http_requests
from datetime import datetime
from pathlib import Path
from typing import Optional
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from config import Config

logger = logging.getLogger(__name__)
CRITICAL_COLUMNS = ["timestamp", "sender_name", "prefix", "message"]
OTHERS_COLUMNS = ["timestamp", "sender_name", "message"]
LLM_COLUMNS = ["timestamp", "analysis"]
SHEET_CRITICAL = "critical"
SHEET_WARNING = "warning"
SHEET_OTHERS = "others"
SHEET_LLM = "LLM"

_profile_cache: dict[str, str] = {}
DELIMITERS = (",", "，")


def _daily_path(date: Optional[datetime] = None) -> Path:
    if date is None:
        date = datetime.now()
    filename = f"line_archive_{date.strftime('%Y%m%d')}.xlsx"
    Config.ensure_dirs()
    return Config.ARCHIVE_DIR / filename


def _get_sheet_name(prefix: str) -> str:
    cleaned = prefix.lower().strip()
    if cleaned.startswith("critical"):
        return SHEET_CRITICAL
    elif cleaned.startswith("warning"):
        return SHEET_WARNING
    return SHEET_OTHERS


def get_user_display_name(user_id: str) -> str:
    if user_id in _profile_cache:
        return _profile_cache[user_id]
    if not Config.LINE_CHANNEL_ACCESS_TOKEN:
        logger.warning("No LINE_CHANNEL_ACCESS_TOKEN, using user_id")
        _profile_cache[user_id] = user_id
        return user_id
    try:
        url = f"https://api.line.me/v2/bot/profile/{user_id}"
        headers = {"Authorization": f"Bearer {Config.LINE_CHANNEL_ACCESS_TOKEN}"}
        resp = http_requests.get(url, headers=headers, timeout=5)
        logger.info("LINE profile API %s -> HTTP %d", user_id, resp.status_code)
        if resp.status_code == 200:
            display_name = resp.json().get("displayName", user_id)
            _profile_cache[user_id] = display_name
            logger.info("Display name: %s -> %s", user_id, display_name)
            return display_name
        else:
            logger.warning("LINE profile API returned %d: %s", resp.status_code, resp.text[:200])
    except Exception as e:
        logger.exception("Failed to fetch LINE profile for %s: %s", user_id, e)
    _profile_cache[user_id] = user_id
    return user_id


def split_message(message: str) -> tuple[str, str]:
    for d in DELIMITERS:
        if d in message:
            parts = message.split(d, 1)
            return parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""
    return "", message


def _ensure_workbook(path: Path) -> Workbook:
    if path.exists():
        wb = load_workbook(str(path))
        for sn in wb.sheetnames:
            if sn == SHEET_LLM:
                continue
            ws = wb[sn]
            if ws.max_row >= 1:
                headers = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]
                if headers == ["timestamp", "sender_name", "sender_user_id", "message"]:
                    ws.cell(row=1, column=1).value = "timestamp"
                    ws.cell(row=1, column=2).value = "sender_name"
                    ws.delete_cols(3)
                    if sn in (SHEET_CRITICAL, SHEET_WARNING):
                        ws.cell(row=1, column=3).value = "prefix"
                        ws.cell(row=1, column=4).value = "message"
                        for row_idx in range(2, ws.max_row + 1):
                            old_msg = ws.cell(row=row_idx, column=3).value or ""
                            prefix, content = split_message(str(old_msg))
                            ws.cell(row=row_idx, column=3).value = prefix
                            ws.cell(row=row_idx, column=4).value = content
                    logger.info("Migrated sheet [%s] (removed sender_user_id)", sn)
        if SHEET_LLM not in wb.sheetnames:
            ws = wb.create_sheet(title=SHEET_LLM)
            ws.append(LLM_COLUMNS)
            bold = Font(bold=True)
            for ci in range(1, len(LLM_COLUMNS) + 1):
                ws.cell(row=1, column=ci).font = bold
        wb.save(str(path))
        return load_workbook(str(path))

    wb = Workbook()
    default_ws = wb.active
    wb.remove(default_ws)
    bold = Font(bold=True)
    for sheet_name, cols in [(SHEET_CRITICAL, CRITICAL_COLUMNS), (SHEET_WARNING, CRITICAL_COLUMNS), (SHEET_OTHERS, OTHERS_COLUMNS)]:
        ws = wb.create_sheet(title=sheet_name)
        ws.append(cols)
        for col_idx in range(1, len(cols) + 1):
            ws.cell(row=1, column=col_idx).font = bold
    ws_llm = wb.create_sheet(title=SHEET_LLM)
    ws_llm.append(LLM_COLUMNS)
    for col_idx in range(1, len(LLM_COLUMNS) + 1):
        ws_llm.cell(row=1, column=col_idx).font = bold
    wb.save(str(path))
    return load_workbook(str(path))


def get_sheet_rows(path: Path, sheet_name: str) -> list[list[str]]:
    if not path.exists():
        return []
    try:
        wb = load_workbook(str(path))
        if sheet_name not in wb.sheetnames:
            return []
        ws = wb[sheet_name]
        rows = []
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                continue
            rows.append([str(c) if c is not None else "" for c in row])
        return rows
    except Exception:
        logger.exception("Failed to read sheet %s from %s", sheet_name, path)
        return []


def archive_message(timestamp: str, sender_name: str, message: str) -> str:
    sheet_name = _get_sheet_name(message)
    path = _daily_path()
    try:
        wb = _ensure_workbook(path)
        ws = wb[sheet_name]
        if sheet_name in (SHEET_CRITICAL, SHEET_WARNING):
            prefix, content = split_message(message)
            ws.append([timestamp, sender_name, prefix, content])
        else:
            ws.append([timestamp, sender_name, message])
        wb.save(str(path))
        logger.info("Archived to [%s] %s", sheet_name, path.name)
        return sheet_name
    except Exception:
        logger.exception("Failed to archive message to %s", path)
        raise


def write_llm_analysis(path: Path, analysis: str) -> None:
    try:
        wb = load_workbook(str(path))
        if SHEET_LLM not in wb.sheetnames:
            ws = wb.create_sheet(title=SHEET_LLM)
            ws.append(LLM_COLUMNS)
            bold = Font(bold=True)
            for ci in range(1, len(LLM_COLUMNS) + 1):
                ws.cell(row=1, column=ci).font = bold
        else:
            ws = wb[SHEET_LLM]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws.append([timestamp, analysis])
        wb.save(str(path))
        logger.info("LLM analysis written to %s", path.name)
    except Exception:
        logger.exception("Failed to write LLM analysis to %s", path)


def clear_archive(date_str: Optional[str] = None) -> bool:
    path = _daily_path() if not date_str else Config.ARCHIVE_DIR / f"line_archive_{date_str}.xlsx"
    if not path.exists():
        return True
    try:
        wb = Workbook()
        default_ws = wb.active
        wb.remove(default_ws)
        bold = Font(bold=True)
        for sheet_name, cols in [(SHEET_CRITICAL, CRITICAL_COLUMNS), (SHEET_WARNING, CRITICAL_COLUMNS), (SHEET_OTHERS, OTHERS_COLUMNS)]:
            ws = wb.create_sheet(title=sheet_name)
            ws.append(cols)
            for col_idx in range(1, len(cols) + 1):
                ws.cell(row=1, column=col_idx).font = bold
        ws_llm = wb.create_sheet(title=SHEET_LLM)
        ws_llm.append(LLM_COLUMNS)
        for col_idx in range(1, len(LLM_COLUMNS) + 1):
            ws_llm.cell(row=1, column=col_idx).font = bold
        wb.save(str(path))
        logger.info("Cleared archive: %s", path.name)
        return True
    except Exception:
        logger.exception("Failed to clear archive %s", path)
        return False


def get_archive_path(date_str: Optional[str] = None) -> Optional[Path]:
    if date_str:
        path = Config.ARCHIVE_DIR / f"line_archive_{date_str}.xlsx"
    else:
        path = _daily_path()
    return path if path.exists() else None
