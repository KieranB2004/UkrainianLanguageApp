import os
import tempfile
import re
from difflib import SequenceMatcher
from typing import Optional, Dict, Any

import speech_recognition as sr

from utils.semantic_model import similarity, normalize

try:
    from faster_whisper import WhisperModel
except Exception:
    WhisperModel = None


def _get_model():
    if WhisperModel is None:
        return None
    model_name = os.getenv("WHISPER_MODEL", "small")
    device = os.getenv("WHISPER_DEVICE", "cpu")
    compute_type = os.getenv("WHISPER_COMPUTE", "int8")
    try:
        return WhisperModel(model_name, device=device, compute_type=compute_type)
    except Exception:
        return None


MODEL = _get_model()


def record_microphone(seconds: int = 4, phrase_time_limit: Optional[int] = None) -> str:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.4)
        audio = recognizer.listen(source, timeout=max(seconds + 2, 5), phrase_time_limit=phrase_time_limit or seconds)

    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    with open(path, "wb") as f:
        f.write(audio.get_wav_data())
    return path


def transcribe_with_whisper(audio_path: str) -> str:
    if MODEL is None:
        try:
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)
            return recognizer.recognize_google(audio)
        except Exception:
            return ""

    try:
        segments, _info = MODEL.transcribe(audio_path, vad_filter=True, beam_size=1)
        text = " ".join((seg.text or "").strip() for seg in segments).strip()
        return text
    except Exception:
        return ""


def score_pronunciation(target_text: str, audio_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns a proxy pronunciation score based on Whisper transcription + similarity.
    Not true phoneme scoring.
    """
    cleanup = False
    if audio_path is None:
        audio_path = record_microphone()
        cleanup = True

    try:
        transcript = transcribe_with_whisper(audio_path)
        target_n = normalize(target_text)
        transcript_n = normalize(transcript)

        if not target_n:
            return {"score": 0.0, "transcript": transcript, "feedback": "No target text provided."}

        lexical = SequenceMatcher(None, transcript_n, target_n).ratio()
        semantic = similarity(transcript_n, target_n)

        score = max(0.0, min(1.0, 0.6 * lexical + 0.4 * semantic))
        if score >= 0.85:
            feedback = "Strong pronunciation match."
        elif score >= 0.70:
            feedback = "Good match, but there is room to tighten pronunciation."
        elif score >= 0.50:
            feedback = "Partial match. Repeat it more clearly."
        else:
            feedback = "Weak match. Slow down and try again."

        return {
            "score": score,
            "transcript": transcript,
            "target": target_text,
            "feedback": feedback,
        }
    finally:
        if cleanup and audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception:
                pass