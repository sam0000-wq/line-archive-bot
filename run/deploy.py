# -*- coding: utf-8 -*-
"""
deploy.py - One-click deploy: test -> git push -> Render deploy
Usage:
    python deploy.py              # interactive
    python deploy.py --auto       # fully automated (no prompts)
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("deploy")

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent


def run(cmd: list[str], cwd: Path = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd or ROOT_DIR), capture_output=True, text=True)


def step_git_push() -> bool:
    run(["git", "add", "-A"])
    status = run(["git", "status", "--porcelain"])
    if status.stdout.strip():
        run(["git", "commit", "-m", f"Auto-deploy: {time.strftime('%Y-%m-%d %H:%M:%S')}"])
        logger.info("Committed changes.")
    else:
        logger.info("No changes to commit.")
    result = run(["git", "push", "origin", "main"])
    if result.returncode != 0:
        logger.error("git push failed: %s", result.stderr.strip())
        return False
    logger.info("Pushed to GitHub.")
    return True


def step_render_deploy() -> bool:
    api_key = os.environ.get("RENDER_API_KEY", "")
    service_id = os.environ.get("RENDER_SERVICE_ID", "")
    if not api_key or not service_id:
        logger.warning("RENDER_API_KEY or RENDER_SERVICE_ID not set, skipping Render deploy.")
        return False
    import requests
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    url = f"https://api.render.com/v1/services/{service_id}/deploys"
    resp = requests.post(url, headers=headers, json={}, timeout=30)
    if resp.status_code not in (200, 201, 202):
        logger.error("Render API error: %d %s", resp.status_code, resp.text)
        return False
    deploy_id = resp.json().get("id") or resp.json()[0].get("deploy", {}).get("id", "unknown")
    logger.info("Render deploy triggered: %s", deploy_id)

    logger.info("Waiting for deploy to finish...")
    for _ in range(60):
        time.sleep(5)
        r = requests.get(f"https://api.render.com/v1/services/{service_id}/deploys?limit=1",
                         headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
        data = r.json()
        status = data[0]["deploy"]["status"] if data else "unknown"
        if status == "live":
            logger.info("Deploy live!")
            return True
        elif status in ("failed", "canceled"):
            logger.error("Deploy failed: %s", status)
            return False
    logger.warning("Deploy timeout (5min). Check Render dashboard.")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true")
    args = parser.parse_args()

    logger.info("=== LINE Archive Bot - Deploy ===")
    logger.info("[1/2] git push...")
    if not step_git_push():
        return 1
    logger.info("[2/2] Render deploy...")
    step_render_deploy()
    logger.info("=== Done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
