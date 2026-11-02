import unittest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from app.config import Settings
from app.providers import ProviderError, _request_chat, chat


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
    @patch("app.providers.urlopen")
    def test_disables_thinking_for_qwen35_models(self, open_url):
        response = Mock()
        response.read.return_value = b'{"message":{"content":"hello"}}'
        open_url.return_value.__enter__.return_value = response

        result = _request_chat(
            "ollama",
            [{"role": "user", "content": "hi"}],
            settings(ollama_model="qwen3.5:4b"),
        )

        payload = json.loads(open_url.call_args.args[0].data)
        self.assertEqual(open_url.call_args.args[0].full_url, "http://localhost:11434/api/chat")
        self.assertIs(payload["think"], False)
        self.assertEqual(payload["options"]["num_predict"], 512)
        self.assertEqual(result, "hello")

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
