"""
Audio Extraction Service

Transcribes audio via Whisper ASR webservice.
"""

import os
import httpx

# Whisper ASR service URL (from docker-compose)
WHISPER_HOST = os.getenv("WHISPER_HOST", "http://whisper-asr:9000")


async def extract_from_audio(audio_data: bytes, filename: str = "audio.wav") -> str:
    """
    Transcribe audio to text via Whisper ASR service.
    
    Args:
        audio_data: Raw audio bytes (wav, mp3, etc.)
        filename: Original filename for content-type detection
    
    Returns:
        Transcribed text
    """
    # Determine content type from extension
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "wav"
    content_types = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "m4a": "audio/mp4",
        "flac": "audio/flac",
        "ogg": "audio/ogg",
        "webm": "audio/webm",
    }
    content_type = content_types.get(ext, "audio/wav")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # POST to Whisper ASR service
        response = await client.post(
            f"{WHISPER_HOST}/asr",
            params={
                "encode": "true",
                "task": "transcribe",
                "output": "txt",
            },
            files={
                "audio_file": (filename, audio_data, content_type)
            }
        )
        response.raise_for_status()
        return response.text.strip()

