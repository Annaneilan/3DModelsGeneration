#!/bin/bash
echo "Starting server"
source /home/ubuntu/app/venv/bin/activate
cd /home/ubuntu/app/Server
uvicorn server:app --host 0.0.0.0 --port 8000