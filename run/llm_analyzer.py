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


def analyze_messages(critical: list[str], warning: list[str], report: list[str] = None, others: list[str] = None) -> str:
    if not critical and not warning and not report and not others:
        return "今日無需分析之訊息"

    parts = []
    if critical:
        parts.append("=== CRITICAL（重大異常）===")
        for i, m in enumerate(critical[-20:], 1):
            parts.append(f"  C{i}. {m}")
    if warning:
        parts.append("=== WARNING（警告事項）===")
        for i, m in enumerate(warning[-20:], 1):
            parts.append(f"  W{i}. {m}")
    if report:
        parts.append("=== REPORT（班報/回報）===")
        for i, m in enumerate(report[-20:], 1):
            parts.append(f"  R{i}. {m}")
    if others:
        parts.append("=== OTHERS（一般回報）===")
        for i, m in enumerate(others[-20:], 1):
            parts.append(f"  O{i}. {m}")

    prompt = (
        "你是資深製造業廠務分析師，產出簡潔專業的分析報告。\n\n"
        "## 絕對規則（違反即失敗）\n"
        "1. 嚴禁編造任何訊息中沒有的數據。停機時間、產能損失、良率影響、預計完成時間、負責單位——若原始訊息沒寫，一律寫「未提供」\n"
        "2. 同一個問題可能出現在多個 section（CRITICAL/WARNING/REPORT），必須合併成一條說明，不可重複列出\n"
        "3. 行動方案中，預計完成時間和負責單位若訊息未提供，寫「未提供」，不可自行填入任何數字或單位名稱\n"
        "4. 報告總長度控制在 25 行以內\n\n"
        "## 輸入訊息\n"
        + "\n".join(parts)
        + "\n\n"
        "## 輸出格式（嚴格遵循，不可偏離）\n\n"
        "【摘要】\n"
        "CRITICAL X項 | WARNING Y項 | REPORT Z項\n"
        "產線狀態：（正常/輕微受影響/嚴重受影響/停線）\n\n"
        "【CRITICAL 分析】\n"
        "相同設備/站點的問題合併為一條，每條用1句話：問題描述+建議優先順序（P1/P2/P3）\n\n"
        "【WARNING 分析】\n"
        "每項1句話：問題+建議\n\n"
        "【REPORT 摘要】\n"
        "1-2句話總結\n\n"
        "【行動方案】\n"
        "依 P1→P2→P3 排列，格式：序號. 行動項目\n"
        "不可自行填入負責單位和預計完成時間\n\n"
        "【風險評估】\n"
        "短期風險 + 預防措施（各1-2句）\n\n"
        "用繁體中文回答。"
    )

    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2000,
        )
        result = resp.choices[0].message.content or ""
        tokens = resp.usage.total_tokens if resp.usage else 0
        logger.info("LLM analysis complete (%d tokens)", tokens)
        return result
    except Exception:
        logger.exception("LLM analysis failed")
        return "LLM 分析暫時無法使用"
