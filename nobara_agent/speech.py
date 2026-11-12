import io
import queue
import time
import wave

import numpy as np

from .config import cfg

RATE = 16000
OUT_RATE = 24000

VOICES = {
    "Aoede": "leve e clara",
    "Puck": "animada e divertida",
    "Charon": "calma e informativa",
    "Kore": "firme e confiante",
    "Fenrir": "energética e intensa",
    "Leda": "jovem e clara",
    "Orus": "grave e sólida",
    "Zephyr": "brilhante e arejada",
}


def record_until_silence(max_seconds: float = 15.0, silence_seconds: float = 1.2,
                         threshold: float = 400.0) -> bytes:
    import sounddevice as sd

    chunks = []
    q = queue.Queue()

    def callback(indata, frames, time_info, status):
        q.put(indata.copy())

    with sd.InputStream(samplerate=RATE, channels=1, dtype="int16",
                        blocksize=1024, callback=callback):
        started = False
        silent = 0
        t0 = time.monotonic()
        while time.monotonic() - t0 < max_seconds:
            try:
                data = q.get(timeout=0.5)
            except queue.Empty:
                continue
            chunks.append(data)
            rms = float(np.sqrt(np.mean(data.astype(np.float32) ** 2)))
            if rms > threshold:
                started = True
                silent = 0
            elif started:
                silent += 1
                if silent >= RATE / 1024 * silence_seconds:
                    break

    if not chunks:
        return b""

    pcm = np.concatenate(chunks).astype(np.int16).tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(pcm)
    return buf.getvalue()


def transcribe(client, wav_bytes: bytes) -> str:
    from google.genai import types

    if not wav_bytes:
        return ""
    res = client.models.generate_content(
        model=cfg.text_model,
        contents=[
            types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav"),
            "Transcreva este áudio em português brasileiro, mantendo gírias e o "
            "jeito natural de falar. Responda SOMENTE com a transcrição, sem "
            "nenhum comentário.",
        ],
    )
    return (res.text or "").strip()


def speak(client, text: str, voice: str) -> None:
    from google.genai import types
    import sounddevice as sd

    if not text.strip():
        return
    res = client.models.generate_content(
        model=cfg.tts_model,
        contents=f"Fale em português brasileiro, com entonação natural e "
                 f"descontraída, como um amigo conversando:\n{text}",
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice))),
        ),
    )
    data = None
    for part in res.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            data = part.inline_data.data
            break
    if not data:
        return
    audio = np.frombuffer(data, dtype=np.int16)
    sd.play(audio, OUT_RATE)
    sd.wait()
