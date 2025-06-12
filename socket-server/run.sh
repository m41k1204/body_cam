#!/bin/bash
echo "🔁 Iniciando servidor TCP en puerto 9001..."
source .env 2>/dev/null
python3 tcp_image_server.py
