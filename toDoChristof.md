


alle orchestrator scripte in flask endpoints 

frontend adden






#den legacy token stellt man unter organisation mittels api token settings an
#dann findet man ihn unter dem user icon unter account und settings 




#modell laden: docker compose exec orchestrator python load_ollama_models.py


Frontend Button / Action	Command to Trigger	Purpose
🔄 Convert PDFs to HTML	docker exec -it docling bash /app/convert_pdfs.sh	Converts all PDFs in /pdfs/ to HTML using Docling
🚀 Create New Label Studio Project	docker compose run --rm orchestrator python create_project.py	Creates a new project using .env settings + questions_and_labels.json
📤 Upload Tasks (HTMLs)	docker compose run --rm orchestrator python upload_tasks.py	Uploads HTMLs as tasks into the project
🤖 Run Prelabeling (LLM)	docker compose exec orchestrator python batch_requests.py	Calls the ML backend with HTML DOMs and questions
✅ Accept Predictions as Annotations	docker compose exec orchestrator python accept_predictions_as_annotations.py	Moves predictions into LS annotations
🔬 Run Evaluation (Compare GT vs Predictions)	docker compose exec orchestrator python compare_predictions_with_annotations.py	Compares 2 LS projects and outputs metrics + CSV