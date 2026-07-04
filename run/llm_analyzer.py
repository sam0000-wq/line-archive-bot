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


def analyze_messages(critical: list[str], warning: list[str], others: list[str] = None) -> str:
    if not critical and not warning and not others:
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
    if others:
        parts.append("=== OTHERS（一般回報）===")
        for i, m in enumerate(others[-20:], 1):
            parts.append(f"  O{i}. {m}")

    prompt = (
        "你是一位資深製造業廠務分析師，專精於半導體/電子製造產線管理。\n"
        "請根據以下產線即時回報訊息，產出一份專業的【產線異常分析報告】。\n\n"
        "## 輸入訊息\n"
        + "\n".join(parts)
        + "\n\n"
        "## 輸出格式（必須嚴格依循，不可偏離）\n\n"
        "### 一、摘要總覽\n"
        "- 統計：CRITICAL X項、WARNING Y項、一般 Z項\n"
        "- 影響範圍：（設備/製程/人員/物料/環境）\n"
        "- 產線狀態：（正常/輕微受影響/嚴重受影響/停線）\n\n"
        "### 二、CRITICAL 重大異常分析\n"
        "逐一列出每項 CRITICAL 訊息，格式如下：\n"
        "1. **問題描述**：<描述>\n"
        "   - 可能 root cause：<至少2個可能原因>\n"
        "   - 影響評估：停機時間約X小時，產能損失約X%，良率影響約X%\n"
        "   - 建議處理優先順序：P1/P2/P3\n\n"
        "### 三、WARNING 警告事項分析\n"
        "逐一列出每項 WARNING 訊息，格式如下：\n"
        "1. **異常現象**：<描述>\n"
        "   - 預防性建議：<避免升級為 CRITICAL 的建議>\n"
        "   - 監控頻率建議：<具體監控時間間隔>\n\n"
        "### 四、行動方案（Action Items）\n"
        "| 項次 | 行動項目 | 負責單位 | 優先順序 | 預計完成時間 |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| 1 | <行動項目> | <負責單位> | P1/P2/P3 | <時間> |\n\n"
        "### 五、風險評估\n"
        "- 短期風險（24hr內）：<具體風險>\n"
        "- 中期風險（本週內）：<具體風險>\n"
        "- 建議預防措施：<具體措施>\n\n"
        "請用繁體中文回答，專業且簡潔。"
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
