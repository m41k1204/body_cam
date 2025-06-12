import socket
import os
import boto3
from datetime import datetime
from dotenv import load_dotenv

# Cargar .env si existe
load_dotenv()

# Configuración
PORT = 9001
BUCKET_NAME = os.getenv("BUCKET_NAME")
UPLOAD_PREFIX = "images/"

# Cliente de S3
s3 = boto3.client('s3')

os.makedirs("tmp_images", exist_ok=True)

def save_to_s3(filename, local_path):
    s3_key = f"{UPLOAD_PREFIX}{filename}"
    s3.upload_file(local_path, BUCKET_NAME, s3_key)
    print(f"✅ Subido a S3: s3://{BUCKET_NAME}/{s3_key}")

def handle_connection(conn):
    try:
        name_size = int.from_bytes(conn.recv(2), 'big')
        filename = conn.recv(name_size).decode()
        img_size = int.from_bytes(conn.recv(4), 'big')
        print(f"📦 Recibiendo {filename} ({img_size} bytes)")

        img_data = b''
        while len(img_data) < img_size:
            chunk = conn.recv(4096)
            if not chunk:
                break
            img_data += chunk

        local_path = os.path.join("tmp_images", filename)
        with open(local_path, 'wb') as f:
            f.write(img_data)

        save_to_s3(filename, local_path)
        conn.sendall(b'OK')
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.sendall(b'ERROR')

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('0.0.0.0', PORT))
    s.listen()
    print(f"🟢 Servidor escuchando en puerto {PORT}...")

    while True:
        conn, addr = s.accept()
        print(f"🔗 Conexión desde {addr}")
        handle_connection(conn)
        conn.close()
