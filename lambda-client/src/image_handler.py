import os
import json
import base64
import uuid
import boto3

s3 = boto3.client("s3")
BUCKET = "bodycam-bucket-pi3"

def lambda_handler(event, context):
    # HTTP API v2 manda el body en base64 si es binario
    body = event.get("body", "")
    if event.get("isBase64Encoded", False):
        image_bytes = base64.b64decode(body)
    else:                              # por si el cliente manda binario puro
        image_bytes = body.encode("latin1")

    filename = f"images/{uuid.uuid4()}.jpg"
    s3.put_object(
        Bucket=BUCKET,
        Key=filename,
        Body=image_bytes,
        ContentType="image/jpeg"
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {"message": "Image uploaded OK", "file": filename}
        ),
    }
