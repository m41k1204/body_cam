import json
import os
import urllib.parse

import boto3
from botocore.exceptions import ClientError

# ────────── clientes AWS ──────────
s3          = boto3.client("s3")
bedrock     = boto3.client("bedrock-runtime", region_name="us-east-1")
transcribe  = boto3.client("transcribe")                     
requests    = boto3.client("lambda")  # ← solo para evitar linter si no usas requests

# ────────── variables de entorno ──────────
BUCKET  = os.environ["BUCKET_NAME"]
PREFIX  = os.getenv("TRANSCRIPTS_PREFIX", "transcripts/")

# lista básica; reemplázala por la que necesites
PALABRAS_CLAVE = [
    "arreglar", "ayuda", "coima", "dinero", "plata", "ayudita", "apoyo"
]

# ────────── prompt generator local ──────────
from .prompt_generator import generate_prompt


def lambda_handler(event, _):
    job_name = event["detail"]["TranscriptionJobName"]
    key_json = f"{PREFIX}{job_name}.json"

    # 1) Descargar transcript JSON de S3
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=key_json)
    except ClientError as e:
        print(f"[{job_name}] No se pudo leer {key_json} → {e}")
        raise

    transcript_text = json.loads(obj["Body"].read())["results"]["transcripts"][0]["transcript"]
    print(f"[{job_name}] Texto transcrito: {transcript_text}")

    # 2) Analizar con Nova Lite
    prompt = generate_prompt(transcript_text, PALABRAS_CLAVE)
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ]
    }

    response = bedrock.invoke_model(
        modelId="amazon.nova-lite-v1:0",          
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload)
    )

    model_raw = json.loads(response["body"].read())
    model_text = model_raw["output"]["message"]["content"][0]["text"].strip()
    model_text = model_text.strip("`").replace("json", "").strip()  
    analysis = json.loads(model_text)                               

    if analysis.get("corrupcion") is True:
        job_info   = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        media_uri  = job_info["TranscriptionJob"]["Media"]["MediaFileUri"]  
        parsed     = urllib.parse.urlparse(media_uri)
        bucket, key_audio = parsed.netloc, parsed.path.lstrip("/")

        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key_audio},
            ExpiresIn=3600  # 1 hora
        )
        analysis["audio_url"] = presigned_url

        # if ALERT_URL:
        #     try:
        #         import requests
        #         requests.post(ALERT_URL, json=analysis, timeout=3)
        #     except Exception as e:
        #         print(f"[{job_name}] Error enviando alerta: {e}")
        body =  json.dumps(
                    {
                        "jobId": job_name,
                        "text": transcript_text,
                        "analysis": analysis,
                    }
                )
        print(body)
        
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "jobId": job_name,
                "text": transcript_text,
                "analysis": analysis,
            }
        ),
    }
