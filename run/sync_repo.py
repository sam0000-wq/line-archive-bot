import base64
import logging
import time
from pathlib import Path
from typing import Optional
import requests
from config import Config

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
OWNER = "sam0000-wq"
REPO = "line-archive-data"
BRANCH = "main"
_last_push: dict[str, float] = {}
PUSH_INTERVAL = 60


def _headers():
    return {
        "Authorization": f"Bearer {Config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def _remote_path(date_str: str) -> str:
    return f"line_archive_{date_str}.xlsx"


def _get_file_sha(remote: str) -> Optional[str]:
    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{remote}"
    resp = requests.get(url, headers=_headers())
    if resp.status_code == 200:
        return resp.json()["sha"]
    return None


def push_xlsx(local_path: Path, date_str: str, force: bool = False) -> bool:
    now = time.time()
    last = _last_push.get(date_str, 0)
    if not force and now - last < PUSH_INTERVAL:
        return True

    if not local_path.exists():
        logger.warning("Local file not found: %s", local_path)
        return False

    remote = _remote_path(date_str)
    content_b64 = base64.b64encode(local_path.read_bytes()).decode()

    sha = _get_file_sha(remote)
    data = {
        "message": f"Update archive {date_str}",
        "content": content_b64,
        "branch": BRANCH,
    }
    if sha:
        data["sha"] = sha

    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{remote}"
    resp = requests.put(url, json=data, headers=_headers())

    if resp.status_code in (200, 201):
        _last_push[date_str] = now
        logger.info("Pushed %s to GitHub (%s)", remote, "updated" if sha else "created")
        return True
    else:
        logger.error("Failed to push %s: HTTP %d %s", remote, resp.status_code, resp.text[:200])
        return False


def pull_xlsx(date_str: str, local_path: Path) -> bool:
    remote = _remote_path(date_str)
    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{remote}"
    resp = requests.get(url, headers=_headers())

    if resp.status_code == 404:
        logger.info("No remote file for %s", date_str)
        return False
    if resp.status_code != 200:
        logger.error("Failed to pull %s: HTTP %d", remote, resp.status_code)
        return False

    data = resp.json()
    raw = base64.b64decode(data["content"].replace("\n", ""))
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(raw)
    logger.info("Pulled %s from GitHub (%d bytes)", remote, len(raw))
    return True
