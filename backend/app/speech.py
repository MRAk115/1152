import json
import tempfile
import wave
from pathlib import Path


MAX_AUDIO_BYTES = 25 * 1024 * 1024


def transcribe(audio: bytes, filename: str, provider: str, settings) -> str:
    if not audio:
        raise ValueError("The uploaded audio file is empty.")
    if len(audio) > MAX_AUDIO_BYTES:
        raise ValueError("Audio files must be 25 MB or smaller.")

    suffix = Path(filename).suffix.lower() or ".audio"
    with tempfile.NamedTemporaryFile(suffix=suffix) as audio_file:
        audio_file.write(audio)
        audio_file.flush()
        if provider == "vosk":
            return _transcribe_vosk(Path(audio_file.name), settings.vosk_model_path)
        return _transcribe_whisper(Path(audio_file.name), settings.whisper_model)


def _transcribe_vosk(audio_path: Path, model_path: Path) -> str:
    if not model_path.is_dir():
        raise ValueError(
            f"Vosk model not found at {model_path}. Download a model and set JARVIS_VOSK_MODEL_PATH."
        )
    try:
        from vosk import KaldiRecognizer, Model
    except ImportError as error:
        raise RuntimeError("Vosk is not installed. Run .\\install-speech.ps1.") from error

    try:
        with wave.open(str(audio_path), "rb") as wav_file:
            if wav_file.getnchannels() != 1 or wav_file.getsampwidth() != 2 or wav_file.getframerate() != 16000:
                raise ValueError("Vosk requires mono, 16-bit PCM WAV audio sampled at 16 kHz.")
            recognizer = KaldiRecognizer(Model(str(model_path)), wav_file.getframerate())
            results: list[str] = []
            while chunk := wav_file.readframes(4000):
                if recognizer.AcceptWaveform(chunk):
                    text = json.loads(recognizer.Result()).get("text", "")
                    if text:
                        results.append(text)
            final_text = json.loads(recognizer.FinalResult()).get("text", "")
            if final_text:
                results.append(final_text)
    except wave.Error as error:
        raise ValueError("Vosk requires a valid WAV audio file.") from error
    return " ".join(results).strip()


def _transcribe_whisper(audio_path: Path, model_name: str) -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError as error:
        raise RuntimeError("faster-whisper is not installed. Run .\\install-speech.ps1.") from error

    try:
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(audio_path))
        return " ".join(segment.text.strip() for segment in segments).strip()
    except (OSError, RuntimeError, ValueError) as error:
        raise RuntimeError(f"Whisper transcription failed: {error}") from error
