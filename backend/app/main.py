from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from app.config import get_settings
from app.providers import ProviderError, chat
from app.speech import transcribe

settings = get_settings()
app = FastAPI(title="Jarvis API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str = Field(pattern="^(system|user|assistant)$")
    content: str = Field(min_length=1, max_length=12000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[Message] = Field(min_length=1, max_length=40)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "provider": settings.provider, "speech_provider": settings.speech_provider}


@app.post("/api/chat")
def create_chat(request: ChatRequest) -> dict[str, str | bool]:
    try:
        answer, provider, fallback_used = chat(
            [message.model_dump() for message in request.messages],
            settings,
        )
    except ProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return {"content": answer, "provider": provider, "fallback_used": fallback_used}


@app.post("/api/transcribe")
async def create_transcription(audio: UploadFile = File(...)) -> dict[str, str]:
    try:
        audio_data = await audio.read(25 * 1024 * 1024 + 1)
        text = transcribe(audio_data, audio.filename or "audio", settings.speech_provider, settings)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {"text": text}
