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
        "## 規則\n"
        "1. 嚴禁腦補：停機時間、產能損失等數字只引用訊息中明確寫出的，沒有就寫「訊息未提供」\n"
        "2. 去除重複：相同站點/設備的問題合併說明，不要重複列出\n"
        "3. 重點是【分析判斷】和【行動建議】，不是照抄原始訊息\n"
        "4. 報告要精簡，一份報告控制在 30 行以內\n\n"
        "## 輸入訊息\n"
        + "\n".join(parts)
        + "\n\n"
        "## 輸出格式（嚴格遵循）\n\n"
        "【摘要】\n"
        "CRITICAL X項 | WARNING Y項 | REPORT Z項\n"
        "產線狀態：（正常/輕微受影響/嚴重受影響/停線）\n\n"
        "【CRITICAL 分析】\n"
        "每項用1-2句話說明：問題、影響、建議處理順序（P1/P2/P3）\n"
        "不要重複抄寫原始訊息\n\n"
        "【WARNING 分析】\n"
        "每項用1句話說明：問題和建議\n\n"
        "【REPORT 摘要】\n"
        "用1-2句話總結班報重點\n\n"
        "【行動方案】\n"
        "依優先順序列出具體行動（負責單位、預計完成時間）\n\n"
        "【風險評估】\n"
        "短期風險 + 預防措施\n\n"
        "請用繁體中文回答。"
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
