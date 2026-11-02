import unittest
from pathlib import Path
from unittest.mock import patch

from app.config import Settings
from app.providers import ProviderError, chat


def settings(**overrides):
    values = {
        "provider": "ollama",
        "fallback_provider": "openai",
        "ollama_url": "http://localhost:11434",
        "ollama_model": "qwen2.5:7b",
        "openai_api_key": "test-key",
        "openai_model": "gpt-4o-mini",
        "speech_provider": "vosk",
        "vosk_model_path": Path("model"),
        "whisper_model": "small",
        "cors_origins": ("http://localhost:5173",),
    }
    values.update(overrides)
    return Settings(**values)


class ChatFallbackTests(unittest.TestCase):
    @patch("app.providers._request_chat")
    def test_uses_primary_provider_when_available(self, request_chat):
        request_chat.return_value = "hello"

        result = chat([{"role": "user", "content": "hi"}], settings())

        self.assertEqual(result, ("hello", "ollama", False))
        request_chat.assert_called_once()

    @patch("app.providers._request_chat")
    def test_uses_fallback_when_primary_fails(self, request_chat):
        request_chat.side_effect = [ProviderError("offline"), "cloud reply"]

        result = chat([{"role": "user", "content": "hi"}], settings())

        self.assertEqual(result, ("cloud reply", "openai", True))
        self.assertEqual(request_chat.call_count, 2)

    @patch("app.providers._request_chat", side_effect=ProviderError("offline"))
    def test_reports_failure_when_fallback_is_disabled(self, request_chat):
        with self.assertRaisesRegex(ProviderError, "offline"):
            chat(
                [{"role": "user", "content": "hi"}],
                settings(fallback_provider="none"),
            )
        request_chat.assert_called_once()


if __name__ == "__main__":
    unittest.main()
