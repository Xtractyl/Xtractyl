# 🦕 xtractyl – Extract structured data from messy medical PDFs

**xtractyl** is a modular AI pipeline to pre-label and annotate medical documents (e.g. discharge letters).  
It converts PDFs → HTML → DOM → prelabels them with an LLM → and allows for manual review via Label Studio.

🔍 Built for human-in-the-loop annotation with evaluation & comparison built in.

---

## 🚀 Features

- ✅ Convert medical PDFs into structured HTML via Docling
- 🤖 Prelabel data with an LLM (Ollama: Gemma3 12B by default)
- 🧠 DOM-based XPath mapping and label matching
- 👩‍⚕️ Use Label Studio for human validation
- 🧪 Evaluate predictions vs. ground truth with built-in metrics
- 🐳 Modular Docker architecture
- 🎛️ Simple CLI & frontend trigger points

---

## ⚙️ Setup





## ⚙️ Usage

🦕 xtractyl Frontend Requirements

🎯 Goal

A simple frontend UI that allows the user to:
	1.	Upload PDFs
	2.	Trigger the pipeline (PDF → HTML → DOM → LLM → Label Studio)
  3.  Accept predictions as truth (can be done without human review via below script or by the User within label studio by submit button)
	4.	Optionally trigger evaluation between prediction and ground truth




🧱 1. Frontend Tech Stack

Use any of the following (your choice):
	•	React (recommended)
	•	Svelte / Vue (if preferred)
	•	Flask / FastAPI with Jinja templates (if you want it integrated directly)





✅ Frontend Integration Guide for xtractyl

📦 Central Backend Scripts & Trigger Points


🔄 Convert PDFs to HTML	
curl -X POST http://localhost:5004/docling/convert-folder


# Modell laden (falls nicht schon geladen)
curl -X POST http://localhost:5001/load_models

# Projekt anlegen
curl -X POST http://localhost:5001/create_project

# Tasks hochladen
curl -X POST http://localhost:5001/upload_tasks

# Vorlabeln
curl -X POST http://localhost:5001/prelabel_project

# Prelabels als Annotationen übernehmen
curl -X POST http://localhost:5001/accept_predictions

# Vergleichen mit anderem Projekt
curl http://localhost:5001/compare_predictions

# Finale Annotationen exportieren
curl http://localhost:5001/export_annotations


🗂 Required Files
	•	.env in root – config for project IDs, token, model name, etc.
	•	questions_and_labels.json in orchestrator/ – maps questions to label names for prelabeling














📝 additional Documentation:
For more details on how to use Label Studio (e.g. reviewing annotations, submitting, filtering), visit:
👉 https://labelstud.io/guide










## 📝 Licensing & Attribution

This project is released under the MIT License. It makes use of the following open-source components:

- [Label Studio](https://github.com/heartexlabs/label-studio) (Apache-2.0)
- [Docling](https://github.com/docling/docling) (MIT)
- [Ollama](https://github.com/ollama/ollama) (MIT)
- LLMs like Gemma, which are subject to their own terms from the model provider (e.g., Google)

Please check the [LICENSE](LICENSE) file for more details. 