import time
import requests

def load_ollama_models_main():
    logs = []
    model = "gemma3:12b"

    logs.append(f"📦 Lade Modell {model} nach...")

    while True:
        try:
            response = requests.post("http://ollama:11434/api/pull", json={"name": model})
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

if __name__ == "__main__":
    for line in load_ollama_models_main():
        print(line)