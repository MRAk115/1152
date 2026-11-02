# Jarvis

A local-first assistant starter project with a React + Vite interface and a Python/FastAPI backend. Chat uses Ollama by default and can fall back to OpenAI. Audio transcription is an optional Vosk or faster-whisper workflow; spoken replies use the browser's built-in speech synthesis.

## Requirements

- Python 3.10+
- Node.js 20.19+ and npm
- Ollama for local chat, unless OpenAI is selected as the primary provider

## Quick start (Windows)

1. Copy `.env.example` to `.env` and adjust the provider settings.
2. In PowerShell, run `.\install.ps1`.
3. Start the API with `.\run-backend.ps1`.
4. In a second terminal, start the UI with `.\run-frontend.ps1`.
5. Open <http://localhost:5173>.

For local chat, install Ollama and pull the model configured in `.env`, for example:

```powershell
ollama pull qwen2.5:7b
```

For OpenAI, set `JARVIS_PROVIDER=openai` or leave Ollama primary and set `JARVIS_FALLBACK_PROVIDER=openai`, then add `JARVIS_OPENAI_API_KEY` to `.env`. Never commit `.env`.

## Audio transcription

The UI accepts an audio file and posts it to `POST /api/transcribe`.

- **Vosk** runs locally without a cloud API key. Install the optional speech dependencies with `.\install-speech.ps1`, download a Vosk model, and set `JARVIS_VOSK_MODEL_PATH`. Vosk expects a mono, 16-bit PCM WAV file sampled at 16 kHz.
- **Whisper** uses faster-whisper locally. Set `JARVIS_SPEECH_PROVIDER=whisper`; the selected model is downloaded on first use. It supports common audio formats through its bundled decoder.

Speech recognition libraries and models are optional and are not installed by the default setup. This avoids installing large ML runtimes unless needed.

## API

- `GET /api/health` — service status and configured providers
- `POST /api/chat` — `{ "messages": [{ "role": "user", "content": "Hello" }] }`
- `POST /api/transcribe` — multipart form upload with an `audio` file

The API listens on `http://127.0.0.1:8000`. Interactive API docs are available at <http://127.0.0.1:8000/docs>.

## Development

Run backend tests:

```powershell
$env:PYTHONPATH = "backend"
.\.venv\Scripts\python.exe -m unittest discover -s backend\tests -v
```

Build the frontend:

```powershell
cd frontend
npm run build
```

## Configuration

All configuration is read from environment variables or the root `.env` file. The backend refuses unknown chat providers and reports provider failures instead of silently returning a canned response. CORS is restricted to the configured origins.

## License

This project is provided under the MIT License; see [LICENSE](LICENSE).
