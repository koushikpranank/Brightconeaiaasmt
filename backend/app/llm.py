"""Pluggable LLM client used ONLY to phrase natural-language explanations and
recommendation text. Every number the LLM sees is already computed deterministically
(app/tools/*) and passed in as evidence - the LLM narrates, it does not calculate.

LLM_PROVIDER=mock (default) runs the whole system with zero external calls or API keys,
using template-based text generation, which keeps the demo runnable out of the box.
Switch to openai/anthropic/gemini via .env once a key is available; the agent code never
changes because it only calls `explain(...)`.
"""
from app.config import settings


def _mock_explain(prompt: str, context: dict) -> str:
    lines = [f"{k}: {v}" for k, v in context.items() if v is not None]
    return f"{prompt.strip()} Based on verified data - {'; '.join(lines)}."


def _openai_explain(prompt: str, context: dict) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    full_prompt = f"{prompt}\n\nVerified data (do not alter any numbers):\n{context}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content


def _anthropic_explain(prompt: str, context: dict) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    full_prompt = f"{prompt}\n\nVerified data (do not alter any numbers):\n{context}"
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=400,
        messages=[{"role": "user", "content": full_prompt}],
    )
    return response.content[0].text


def _gemini_explain(prompt: str, context: dict) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    full_prompt = f"{prompt}\n\nVerified data (do not alter any numbers):\n{context}"
    response = model.generate_content(full_prompt)
    return response.text


_PROVIDERS = {
    "mock": _mock_explain,
    "openai": _openai_explain,
    "anthropic": _anthropic_explain,
    "gemini": _gemini_explain,
}


def explain(prompt: str, context: dict) -> str:
    provider = _PROVIDERS.get(settings.llm_provider, _mock_explain)
    try:
        return provider(prompt, context)
    except Exception:
        # Never let narration failures break the deterministic pipeline.
        return _mock_explain(prompt, context)
