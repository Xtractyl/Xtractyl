import requests, time

model = "gemma3:12b"

print(f"📦 Lade Modell {model} nach...")
while True:
    try:
        response = requests.post("http://ollama:11434/api/pull", json={"name": model})
        if response.ok:
            print("✅ Modell erfolgreich geladen.")
            break
        else:
            print(f"⚠️ Fehler beim Laden: {response.text}")
    except Exception as e:
        print(f"⏳ Noch nicht erreichbar: {e}")
    time.sleep(5)