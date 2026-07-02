import logging
from typing import Optional
from openai import OpenAI
from config import Config

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=GROQ_BASE_URL, api_key=Config.GROQ_API_KEY)
    return _client


def analyze_messages(critical: list[str], warning: list[str]) -> str:
    if not critical and not warning:
        return "今日無需分析之訊息"

    parts = []
    if critical:
        parts.append("=== 重要訊息 (critical) ===")
        for m in critical[-20:]:
            parts.append(f"- {m}")
    if warning:
        parts.append("=== 警告訊息 (warning) ===")
        for m in warning[-20:]:
            parts.append(f"- {m}")

    prompt = (
        "你是一個 LINE 群組訊息分析助手。以下是今日收集到的重要與警告訊息，請整理出重點摘要。\n\n"
        + "\n".join(parts)
        + "\n\n請用繁體中文提供：\n1. 重點摘要\n2. 需要採取行動的項目（若無則略過）\n3. 關注趨勢"
    )

    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
        )
        result = resp.choices[0].message.content or ""
        tokens = resp.usage.total_tokens if resp.usage else 0
        logger.info("LLM analysis complete (%d tokens)", tokens)
        return result
    except Exception:
        logger.exception("LLM analysis failed")
        return "LLM 分析暫時無法使用"
