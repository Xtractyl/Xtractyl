import os
import time

import requests

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    f"http://{os.getenv('OLLAMA_CONTAINER_NAME', 'ollama')}:{os.getenv('OLLAMA_PORT', '11434')}",
)


def load_ollama_models_main():
    logs = []
    model = "gemma3:12b"

    logs.append(f"📦 Lade Modell {model} nach...")

    while True:
        try:
            response = requests.post(f"{OLLAMA_URL}/api/pull", json={"name": model})
            if response.ok:
                logs.append("✅ Modell erfolgreich geladen.")
                break
            else:
                logs.append(f"⚠️ Fehler beim Laden: {response.text}")
        except Exception as e:
            logs.append(f"⏳ Noch nicht erreichbar: {e}")
        time.sleep(5)

    return logs


def load_ollama_models_main_wrapper():
    return load_ollama_models_main()
