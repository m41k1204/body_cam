# ───────────────────────── src/audio_handler.py ─────────────────────────
import base64
import boto3
import io
import json
import os
import uuid
import wave

s3         = boto3.client("s3")
transcribe = boto3.client("transcribe")

BUCKET              = os.environ["BUCKET_NAME"]
PREFIX_TRANSCRIPTS  = os.getenv("TRANSCRIPTS_PREFIX", "transcripts/")
LANGUAGE_CODE       = os.getenv("LANGUAGE_CODE", "es-ES")

# Ajusta estos valores si tu ESP32 cambia de formato
SAMPLE_RATE   = int(os.getenv("SAMPLE_RATE" , "8000"))   # Hz
CHANNELS      = int(os.getenv("CHANNELS"    , "1"))      # 1 = mono
SAMPLE_WIDTH  = int(os.getenv("SAMPLE_WIDTH", "1"))      # bytes por muestra (1 → 8 bits PCM)

RAW_CTYPES = {
    "application/octet-stream",
    "binary/octet-stream",
    "audio/pcm",
}

def _raw_pcm_to_wav(raw_bytes: bytes) -> bytes:
    """
    Envuelve audio PCM bruto en un contenedor WAV en memoria.
    Devuelve los bytes WAV listos para subir a S3.
    """
    buff = io.BytesIO()
    with wave.open(buff, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(raw_bytes)
    return buff.getvalue()


def lambda_handler(event, _):
    try:
        # ── 1) Extraer audio ────────────────────────────────────────────
        body = event["body"]
        audio_bytes = base64.b64decode(body) if event.get("isBase64Encoded") else (
            body.encode() if isinstance(body, str) else body
        )

        # ── 2) Detectar Content-Type y convertir si es PCM raw ──────────
        headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
        ctype   = headers.get("content-type", "application/octet-stream").lower()

        if ctype in RAW_CTYPES:
            # Llega como binario crudo → lo envolvemos en WAV
            audio_bytes = _raw_pcm_to_wav(audio_bytes)
            ctype       = "audio/wav"
            ext         = "wav"
        else:
            # Llega ya como audio codificado (wav | mpeg, etc.)
            ext = "mp3" if "mpeg" in ctype else "wav"

        # ── 3) Subir a S3 ───────────────────────────────────────────────
        key_audio = f"audios/{uuid.uuid4()}.{ext}"
        s3.put_object(
            Bucket      = BUCKET,
            Key         = key_audio,
            Body        = audio_bytes,
            ContentType = ctype,
        )

        # ── 4) Lanzar Transcribe ────────────────────────────────────────
        job_name = f"job-{uuid.uuid4()}"
        transcribe.start_transcription_job(
            TranscriptionJobName = job_name,
            Media                = {"MediaFileUri": f"s3://{BUCKET}/{key_audio}"},
            MediaFormat          = "wav",                 # ahora siempre usamos WAV
            OutputBucketName     = BUCKET,
            OutputKey            = f"{PREFIX_TRANSCRIPTS}{job_name}.json",
            LanguageCode         = LANGUAGE_CODE,
        )

        return {"statusCode": 202, "body": json.dumps({"jobId": job_name})}

    except Exception as exc:
        return {"statusCode": 500, "body": str(exc)}
