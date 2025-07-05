#!/bin/bash

# Lade .env ins aktuelle Shell Environment
set -o allexport
source /app/.env
set +o allexport

MODEL=${OLLAMA_MODEL:-llama3}  # Fallback auf llama3

echo "🔁 Warten bis Ollama erreichbar ist..."
until curl -s http://ollama:11434/ > /dev/null; do
  sleep 2
done

echo "📦 Prüfen, ob Modell '${MODEL}' bereit ist..."
while true; do
  if curl -s -X POST http://ollama:11434/api/show -H "Content-Type: application/json" -d "{\"name\":\"${MODEL}\"}" | grep -q "modelfile"; then
    echo "✅ Modell '${MODEL}' ist bereit."
    break
  else
    echo "⏳ Modell noch nicht verfügbar, warte..."
    sleep 5
  fi
done

echo "🚀 Starte Flask Backend mit Modell '${MODEL}'..."
exec python -u app.py