# -*- coding: utf-8 -*-
"""Flask webhook server for LINE message archiving."""

import logging
import os
import sys
from datetime import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, request, abort, send_file
from linebot.v3 import SignatureValidator
from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import MessagingApi, ApiClient, Configuration, TextMessage, PushMessageRequest
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent, JoinEvent
from archiver import archive_message
from config import Config
from mailer import send_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

configuration = Configuration(access_token=Config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(Config.LINE_CHANNEL_SECRET)
scheduler = BackgroundScheduler()
TAIPEI_TZ = pytz.timezone("Asia/Taipei")

detected_group_ids: list[str] = []
last_messages: list[dict] = []


def send_line_report(today: str) -> None:
    if not Config.TARGET_GROUP_ID:
        logger.warning("TARGET_GROUP_ID not set, skipping LINE group notification")
        return
    url = f"{Config.BASE_URL}/files/line_archive_{today}.xlsx"
    msg = f"📋 {today} 群組訊息歸檔報告已產生\n下載: {url}"
    try:
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.push_message(
                PushMessageRequest(
                    to=Config.TARGET_GROUP_ID,
                    messages=[TextMessage(text=msg)],
                )
            )
        logger.info("LINE group notification sent for %s", today)
    except Exception:
        logger.exception("Failed to send LINE group notification for %s", today)


def scheduled_report_job() -> None:
    today = datetime.now(TAIPEI_TZ).strftime("%Y%m%d")
    logger.info("Scheduled report triggered for %s", today)
    success = send_report(today)
    if success:
        logger.info("Scheduled report sent OK for %s", today)
    else:
        logger.error("Scheduled report FAILED for %s", today)
    send_line_report(today)


@app.route("/files/<path:filename>", methods=["GET"])
def serve_file(filename: str):
    from pathlib import Path as _Path
    filepath = Config.ARCHIVE_DIR / _Path(filename).name
    if not filepath.exists() or not filepath.is_file():
        abort(404, "File not found")
    return send_file(str(filepath), as_attachment=True)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": datetime.now(TAIPEI_TZ).isoformat()})


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    logger.debug("Webhook received: %s", body[:200])
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.warning("Invalid signature. Ensure webhook URL is set correctly in LINE Developers Console. rejected")
        abort(400, "Invalid signature. Ensure webhook URL is set correctly in LINE Developers Console.")
    return jsonify({"status": "ok"})


@app.route("/group-id", methods=["GET"])
def get_group_id():
    return jsonify({
        "detected_group_ids": list(dict.fromkeys(detected_group_ids)),
        "last_messages": last_messages[-10:],
    })

@app.route("/send-report", methods=["POST"])
def trigger_report():
    today = datetime.now(TAIPEI_TZ).strftime("%Y%m%d")
    success = send_report(today)
    if success:
        return jsonify({"status": "ok", "date": today})
    return jsonify({"status": "error", "date": today}), 500


@handler.add(JoinEvent)
def handle_join(event: JoinEvent) -> None:
    source = event.source
    group_id = getattr(source, "group_id", None)
    if group_id:
        logger.info("[GROUP ID DETECTED] groupId=%s (via join event)", group_id)
        if group_id not in detected_group_ids:
            detected_group_ids.append(group_id)

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event: MessageEvent) -> None:
    message: TextMessageContent = event.message
    source = event.source
    group_id = getattr(source, "group_id", None)
    if group_id:
        logger.info("[GROUP ID DETECTED] groupId=%s", group_id)
        if group_id not in detected_group_ids:
            detected_group_ids.append(group_id)
        last_messages.append({
            "group_id": group_id,
            "user_id": source.user_id,
            "text": message.text[:100],
            "timestamp": datetime.fromtimestamp(event.timestamp / 1000.0, tz=TAIPEI_TZ).isoformat(),
        })
    if Config.TARGET_GROUP_ID and group_id != Config.TARGET_GROUP_ID:
        logger.debug("Ignoring message from non-target group: %s", group_id)
        return
    if not Config.TARGET_GROUP_ID and not group_id:
        logger.debug("Ignoring non-group message (no TARGET_GROUP_ID set)")
        return
    timestamp = datetime.fromtimestamp(event.timestamp / 1000.0, tz=TAIPEI_TZ).strftime("%Y-%m-%d %H:%M:%S")
    try:
        sheet = archive_message(
            timestamp=timestamp,
            sender_name=event.source.user_id or "unknown",
            sender_user_id=event.source.user_id or "unknown",
            message=message.text,
        )
        logger.info("Archived message from %s to sheet [%s]", event.source.user_id, sheet)
    except Exception:
        logger.exception("Failed to archive message")


def init_scheduler() -> None:
    scheduler.add_job(
        func=scheduled_report_job,
        trigger="cron",
        hour=20,
        minute=0,
        timezone=TAIPEI_TZ,
        id="daily_report",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started: daily report at 20:00 Asia/Taipei")


def create_app() -> Flask:
    Config.ensure_dirs()
    missing = Config.validate()
    if missing:
        logger.warning("Missing environment variables: %s", ", ".join(missing))
    init_scheduler()
    return app


if __name__ == "__main__":
    create_app()
    port = Config.APP_PORT
    logger.info("Starting local server on 0.0.0.0:%d", port)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)




