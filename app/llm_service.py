import json
import os
from pathlib import Path

from langchain_openai import ChatOpenAI

from app.logger import Timer, log

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "extraction_prompt.txt"


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def get_llm():
    provider = os.getenv("LLM_PROVIDER", "openai")
    model = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    api_key = os.getenv("LLM_API_KEY", "sk-or-v1-placeholder")
    base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")

    default_headers = {}
    referrer = os.getenv("LLM_REFERRER")
    if referrer:
        default_headers["HTTP-Referer"] = referrer

    if provider == "openai":
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            default_headers=default_headers or None,
            temperature=0.1,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def extract_invoice_fields(ocr_text: str) -> dict:
    if not ocr_text.strip():
        log.warning("LLM skipped — empty OCR text")
        return {"error": "No text extracted from document"}

    prompt_template = load_prompt()
    user_message = prompt_template.replace("{text}", ocr_text)

    llm = get_llm()
    log.info("LLM input: %d characters", len(ocr_text))
    with Timer("llm.invoke"):
        response = llm.invoke([
            ("system", "You extract structured data from OCR invoice text. Return only valid JSON."),
            ("human", user_message),
        ],
        extra_body={"reasoning": {"effort": None}},)
    content = response.content

    try:
        extracted = content.strip()
        if extracted.startswith("```"):
            extracted = extracted.split("\n", 1)[-1].rsplit("\n```", 1)[0]
        result = json.loads(extracted)
        containers = result.get("containers") or []
        nums = [c["number"] for c in containers] if isinstance(containers, list) else containers
        log.info("LLM extracted: do_number=%s consignee=%s depot=%s containers=%s", result.get("do_number"), result.get("consignee"), result.get("depot"), nums)
        return result
    except json.JSONDecodeError:
        log.error("LLM returned invalid JSON: %s", content[:200])
        return {"error": f"LLM returned invalid JSON: {content}"}
