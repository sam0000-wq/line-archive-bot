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
        "你是一位資深製造業廠務分析師。\n"
        "請根據以下產線即時回報訊息，產出一份分析報告。\n\n"
        "## 重要規則\n"
        "- 嚴禁自行推測、補充、腦補任何訊息中沒有的數據\n"
        "- 停機時間、產能損失、良率影響等數字，若訊息中未明確寫出，不得自行填入\n"
        "- 沒有就寫「訊息未提供」\n"
        "- 只能引用訊息中實際出現的內容\n\n"
        "## 輸入訊息\n"
        + "\n".join(parts)
        + "\n\n"
        "## 輸出格式\n\n"
        "### 一、摘要總覽\n"
        "- 統計：CRITICAL X項、WARNING Y項、REPORT Z項、一般 W項\n"
        "- 各項摘要（僅引用訊息原文）\n\n"
        "### 二、CRITICAL 重大異常分析\n"
        "逐一列出每項 CRITICAL 訊息：\n"
        "1. **問題描述**：<照抄訊息原文>\n"
        "   - 可能原因：<根據訊息內容推論，不可編造>\n"
        "   - 建議優先順序：P1/P2/P3\n\n"
        "### 三、WARNING 警告事項分析\n"
        "逐一列出每項 WARNING 訊息：\n"
        "1. **異常現象**：<照抄訊息原文>\n"
        "   - 建議：<根據訊息內容給出建議>\n\n"
        "### 四、REPORT 班報回報摘要\n"
        "總結 REPORT 訊息中的重要資訊（僅引用原文）\n\n"
        "### 五、行動方案\n"
        "根據以上分析列出具體行動項目\n\n"
        "### 六、風險評估\n"
        "- 短期風險：（僅根據訊息內容判斷）\n"
        "- 建議預防措施：\n\n"
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
