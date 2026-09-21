"""Verifies every LLM provider's integration path is wired correctly - the exact request
shape, model name, and response-parsing logic a real API key would exercise - without
requiring a real key or network access. The SDK client is mocked at the point each
provider function imports it; the surrounding call/parse logic is real and runs unmocked.
"""
from unittest.mock import MagicMock, patch

from app.llm import _anthropic_explain, _gemini_explain, _mock_explain, _openai_explain, explain


def test_mock_explain_never_touches_network_and_reports_real_context():
    result = _mock_explain("Summarize this.", {"coverage_days": 5.0, "material": "Steel Plate"})
    assert "coverage_days: 5.0" in result
    assert "material: Steel Plate" in result


@patch("openai.OpenAI")
def test_openai_explain_calls_chat_completions_with_expected_shape(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Five days of coverage remain."))]
    )

    result = _openai_explain("Summarize coverage.", {"coverage_days": 5.0})

    assert result == "Five days of coverage remain."
    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs["model"] == "gpt-4o-mini"
    assert "coverage_days" in kwargs["messages"][0]["content"]


@patch("anthropic.Anthropic")
def test_anthropic_explain_calls_messages_api_with_expected_shape(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(content=[MagicMock(text="Five days of coverage remain.")])

    result = _anthropic_explain("Summarize coverage.", {"coverage_days": 5.0})

    assert result == "Five days of coverage remain."
    _, kwargs = mock_client.messages.create.call_args
    assert kwargs["model"] == "claude-sonnet-5"
    assert "coverage_days" in kwargs["messages"][0]["content"]


@patch("google.genai.Client")
def test_gemini_explain_calls_generate_content_with_expected_shape(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.models.generate_content.return_value = MagicMock(text="Five days of coverage remain.")

    result = _gemini_explain("Summarize coverage.", {"coverage_days": 5.0})

    assert result == "Five days of coverage remain."
    _, kwargs = mock_client.models.generate_content.call_args
    assert kwargs["model"] == "gemini-flash-latest"
    assert "coverage_days" in kwargs["contents"]


def test_explain_falls_back_to_mock_when_provider_raises(monkeypatch):
    """If a real provider call fails (bad key, network down), the pipeline must still get a
    usable narration back instead of crashing the whole agent step."""
    import app.llm as llm_module

    monkeypatch.setattr(llm_module, "_PROVIDERS", {"openai": lambda p, c: (_ for _ in ()).throw(RuntimeError("boom"))})
    monkeypatch.setattr(llm_module.settings, "llm_provider", "openai")

    result = explain("Summarize.", {"material": "Steel Plate"})
    assert "material: Steel Plate" in result
