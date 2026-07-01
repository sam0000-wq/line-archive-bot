# -*- coding: utf-8 -*-
"""Gmail SMTP email module."""

import logging
import smtplib
import ssl
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def _build_message(attachment_path: Optional[Path], date_str: str) -> MIMEMultipart:
    msg = MIMEMultipart()
    msg["From"] = Config.GMAIL_USER
    msg["To"] = Config.REPORT_TO_EMAIL
    msg["Subject"] = f"LINE Archive Report - {date_str}"
    body = f"LINE group message archive for {date_str} is attached.\n\nSent automatically by the LINE Archival System.\n"
    if attachment_path and attachment_path.exists():
        body += f"\nAttachment: {attachment_path.name}\n"
    else:
        body += "\nNo messages were recorded for this date.\n"
    msg.attach(MIMEText(body, "plain", "utf-8"))
    if attachment_path and attachment_path.exists():
        with open(str(attachment_path), "rb") as fh:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(fh.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{attachment_path.name}"')
        msg.attach(part)
    return msg


def send_report(target_date: Optional[str] = None) -> bool:
    if target_date is None:
        target_date = datetime.now().strftime("%Y%m%d")
    archive_path = Config.ARCHIVE_DIR / f"line_archive_{target_date}.xlsx"
    msg = _build_message(attachment_path=archive_path if archive_path.exists() else None, date_str=target_date)
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(Config.GMAIL_USER, Config.GMAIL_APP_PASSWORD)
            server.send_message(msg)
        logger.info("Report sent successfully for %s", target_date)
        return True
    except Exception:
        logger.exception("Failed to send report for %s", target_date)
        return False
