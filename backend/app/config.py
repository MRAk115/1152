import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    provider: str
    fallback_provider: str
    ollama_url: str
    ollama_model: str
    openai_api_key: str
    openai_model: str
    speech_provider: str
    vosk_model_path: Path
    whisper_model: str
    cors_origins: tuple[str, ...]


def get_settings() -> Settings:
    provider = os.getenv("JARVIS_PROVIDER", "ollama").strip().lower()
    fallback_provider = os.getenv("JARVIS_FALLBACK_PROVIDER", "openai").strip().lower()
    speech_provider = os.getenv("JARVIS_SPEECH_PROVIDER", "vosk").strip().lower()
    if provider not in {"ollama", "openai"}:
        raise ValueError("JARVIS_PROVIDER must be 'ollama' or 'openai'.")
    if fallback_provider not in {"none", "ollama", "openai"}:
        raise ValueError("JARVIS_FALLBACK_PROVIDER must be 'none', 'ollama', or 'openai'.")
    if speech_provider not in {"vosk", "whisper"}:
        raise ValueError("JARVIS_SPEECH_PROVIDER must be 'vosk' or 'whisper'.")

    model_path = Path(os.getenv("JARVIS_VOSK_MODEL_PATH", "backend/models/vosk-model-small-en-us-0.15"))
    if not model_path.is_absolute():
        model_path = PROJECT_ROOT / model_path
    origins = tuple(
        origin.strip()
        for origin in os.getenv("JARVIS_CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    )
    return Settings(
        provider=provider,
        fallback_provider=fallback_provider,
        ollama_url=os.getenv("JARVIS_OLLAMA_URL", "http://localhost:11434").rstrip("/"),
        ollama_model=os.getenv("JARVIS_OLLAMA_MODEL", "qwen2.5:7b"),
        openai_api_key=os.getenv("JARVIS_OPENAI_API_KEY", ""),
        openai_model=os.getenv("JARVIS_OPENAI_MODEL", "gpt-4o-mini"),
        speech_provider=speech_provider,
        vosk_model_path=model_path,
        whisper_model=os.getenv("JARVIS_WHISPER_MODEL", "small"),
        cors_origins=origins,
    )
