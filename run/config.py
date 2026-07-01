# -*- coding: utf-8 -*-
"""Configuration loader from environment variables and embedded defaults."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

_dotenv_path = Path(__file__).resolve().parent / ".env"
if _dotenv_path.exists():
    load_dotenv(dotenv_path=str(_dotenv_path), encoding="utf-8")


def _get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


class Config:
    LINE_CHANNEL_SECRET: str = _get_env("LINE_CHANNEL_SECRET", "")
    LINE_CHANNEL_ACCESS_TOKEN: str = _get_env("LINE_CHANNEL_ACCESS_TOKEN", "")
    TARGET_GROUP_ID: str = _get_env("TARGET_GROUP_ID", "")
    GMAIL_USER: str = _get_env("GMAIL_USER", "itsamliu2025@gmail.com")
    GMAIL_APP_PASSWORD: str = _get_env("GMAIL_APP_PASSWORD", "")
    REPORT_TO_EMAIL: str = _get_env("REPORT_TO_EMAIL", "itsamliu2025@gmail.com")
    TZ: str = _get_env("TZ", "Asia/Taipei")
    APP_PORT: int = int(_get_env("PORT", "5000"))
    BASE_DIR: Path = Path(__file__).resolve().parent
    ARCHIVE_DIR: Path = BASE_DIR / "archive"
    LOG_DIR: Path = BASE_DIR / "logs"

    @classmethod
    def ensure_dirs(cls) -> None:
        cls.ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls) -> list[str]:
        missing: list[str] = []
        if not cls.LINE_CHANNEL_SECRET:
            missing.append("LINE_CHANNEL_SECRET")
        if not cls.LINE_CHANNEL_ACCESS_TOKEN:
            missing.append("LINE_CHANNEL_ACCESS_TOKEN")
        if not cls.GMAIL_APP_PASSWORD:
            missing.append("GMAIL_APP_PASSWORD")
        return missing
