## Work in Progress

The results page is still missing.  
The backend requires optimization for accuracy and speed, now that iterative testing is possible via the frontend.  
Both backend and frontend are at the early stages of refactoring.

# 🦕 Xtractyl – Extract structured data from messy medical PDFs

**Xtractyl** is a modular, local, human-in-the-loop AI pipeline that searches unstructured PDF documents for specific cases in your data and builds a structured database from them.  

It converts PDFs → HTML → DOM → pre-labels them with an LLM → allows manual review via Label Studio → and 🦕 **xtracts** them into your database.

🔍 Designed for **privacy-first**, human-validated data extraction with evaluation & comparison tools built in.

---

## 📜 License

Xtractyl is licensed under the **Xtractyl Non-Commercial License v1.1**.  
You are free to use, copy, modify, and distribute this software **only for non-commercial purposes**.  
Any commercial use requires a separate commercial license from the copyright holders.

🔒 **No Commercial Use Allowed Without Permission**  
See the [LICENSE](LICENSE) file for full terms.

---

## 🚀 Features

- 🔒 Keeps all your data local — no cloud processing 
- ✅ Convert medical PDFs into structured HTML via **Docling**  
- 🤖 Pre-label data with an LLM (**Ollama: Gemma3 12B** by default)  
- 🧠 DOM-based XPath mapping and label matching  
- 👩‍⚕️ Human validation with **Label Studio**  
- 🔍 Find specific cases in your documents  
- 🦕 Extract a database from your previously unstructured data  
- 🐳 Modular **Docker** architecture  

---

## 📅 Planned Features

- 🦕 Create dashboards from your Xtractyl-generated database  
- 🧪 Evaluate predictions vs. ground truth with built-in metrics  
- 🎛️ Fine-tune models based on your labeled data 

---

## ⚙️ Setup

### 1. Requirements
Before installing Xtractyl, ensure you have the following installed on your system:

- **Docker** & **Docker Compose**
- **Node.js** (v20 or later)
- **Python** (v3.10 or later)
- **Ollama** (for running local LLMs) → [Ollama installation guide](https://ollama.com/download)

---

### 2. Installation
Clone the repository and start the Docker containers:

```bash
git clone https://github.com/<your-username>/xtractyl.git
cd xtractyl
docker compose up --build
```

---

## 📖 Usage

1. **Open the frontend**  
	Go to: [http://localhost:5173](http://localhost:5173)

2. **Upload your docs** (PDF → HTML conversion)  
   Page: **Upload & Convert** (`/`)  
   - Choose or type a folder name  
   - Select PDFs and click **Upload & Convert**  
   - You can monitor status and cancel a running job

3. **Create a new project** in Label Studio  
   Page: **Create Project** (`/project`)  
   - Save your Label Studio token  
   - Enter project name, questions, and labels  
   - Create the project (ML backend gets attached automatically)

4. **Upload your tasks into the project**  
   Page: **Upload Tasks** (`/tasks`)  
   - Pick the project name  
   - Select the HTML folder (from step 2)  
   - Upload tasks to Label Studio

5. **Start AI prelabeling**  
   Page: **Start Prelabeling** (`/prelabelling`)  
   - (Select LLM, system prompt, and the project)  
   - Start prelabeling and monitor status (cancel if needed)

6. **Review the AI**  
   Page: **Review in Label Studio** (`/review`)  
   - Open Label Studio to validate/correct predictions

7. **Get your results**  
   Page: **Get Results** (`/results`)  
   - Export validated annotations for downstream use

---

### ⏭️ Coming Soon
8. **Evaluate the AI** (`/evaluate`)  
   - Compare predictions vs. ground truth, see metrics

9. **Fine-tune the AI** (`/finetune`) 
   - Use your labeled data to improve model performance

---

## 📝 Additional Documentation
For more details on how to use Label Studio (e.g. reviewing annotations, submitting, filtering), visit:
👉 https://labelstud.io/guide

---

## 📝 Disclaimer / Licensing & Attribution


This project is a private, non-commercial initiative developed independently during personal time.  
It has no connection to any employer or professional affiliation and is provided as-is for research and experimentation.

This project is released under the **Xtractyl Non-Commercial License v1.1**.  
It incorporates the following open-source components:

- [Label Studio](https://github.com/heartexlabs/label-studio) — Apache-2.0 License  
- [Docling](https://github.com/docling/docling) — MIT License  
- [Ollama](https://github.com/ollama/ollama) — MIT License  
- Local LLMs such as Gemma, which are subject to their own license terms from the respective model providers (e.g., Google)

Please refer to the [LICENSE](LICENSE) file for the full license text.