#!/bin/bash

set -e

echo "Starting Ollama..."

ollama serve > /tmp/ollama.log 2>&1 &

echo "Waiting for Ollama..."

until curl -s http://127.0.0.1:11434/api/tags > /dev/null; do
    sleep 2
done

echo "Ollama is ready."

echo "Pulling nomic-embed-text..."
ollama pull nomic-embed-text

echo "Pulling llama3.2..."
ollama pull llama3.2

echo "Starting FastAPI..."

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-7860}"