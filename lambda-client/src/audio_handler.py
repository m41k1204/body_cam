import base64
import boto3
import json
import os
import uuid

s3 = boto3.client("s3")
transcribe = boto3.client("transcribe")

BUCKET = os.environ["BUCKET_NAME"]
PREFIX_TRANSCRIPTS = os.getenv("TRANSCRIPTS_PREFIX", "transcripts/")
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "es-ES")


def lambda_handler(event, _):
    try:
        # ── 1) Extraer bytes del audio ─────────────────────────
        body = event["body"]
        audio_bytes = base64.b64decode(body) if event.get("isBase64Encoded") else (
            body.encode() if isinstance(body, str) else body
        )

        # ── 2) Detectar Content-Type → extensión ──────────────
        headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
        ctype = headers.get("content-type", "audio/wav").lower()
        ext = "mp3" if "mpeg" in ctype else "wav"

        # ── 3) Subir a S3 ──────────────────────────────────────
        key_audio = f"audios/{uuid.uuid4()}.{ext}"
        s3.put_object(
            Bucket=BUCKET,
            Key=key_audio,
            Body=audio_bytes,
            ContentType=ctype,
        )

        # ── 4) Lanzar Transcribe (asíncrono) ───────────────────
        job_name = f"job-{uuid.uuid4()}"
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": f"s3://{BUCKET}/{key_audio}"},
            OutputBucketName=BUCKET,
            OutputKey=f"{PREFIX_TRANSCRIPTS}{job_name}.json",
            LanguageCode=LANGUAGE_CODE,
        )

        return {"statusCode": 202, "body": json.dumps({"jobId": job_name})}

    except Exception as exc:
        return {"statusCode": 500, "body": str(exc)}
