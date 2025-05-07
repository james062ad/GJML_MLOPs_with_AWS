# Step-by-Step Implementation Log

1. Clone & Fork  
**Date:** 2025-05-07  
**Commands run:**  
```bash
# Forked via GitHub UI, then:
git clone https://github.com/james062ad/GJML_MLOPs_with_AWS.git
```  
**Outcome:** Repo cloned into `GJML_MLOPs_with_AWS/`.  
**Notes:** ✅ Clone completed without errors.  
________________________________________

2. Create docs & screenshots folders  
**Date:** 2025-05-07  
**Commands run:**  
```powershell
cd GJML_MLOPs_with_AWS
docker rm -f <none>
mkdir docs
mkdir docs\screenshots
```  
**Outcome:** `docs/` and `docs/screenshots/` directories created.  
**Notes:** ✅ Ready to store logs and screenshots.  
________________________________________

3. Create & activate Python virtual environment  
**Date:** 2025-05-07  
**Commands run:**  
```powershell
cd rag-app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```  
**Outcome:** Virtual environment `.venv` activated (`(.venv)` prompt appears).  
**Notes:** ✅ Isolated Python environment is ready.  
________________________________________

4. Install Python dependencies  
**Date:** 2025-05-07  
**Commands run:**  
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```  
**Outcome:** All packages from `requirements.txt` installed successfully.  
**Notes:** ✅ No missing dependency errors.  
________________________________________

5. Install extra Python packages  
**Date:** 2025-05-07  
**Commands run:**  
```powershell
pip install openai boto3 streamlit
```  
**Outcome:** `openai`, `boto3`, and `streamlit` installed.  
**Notes:** ✅ Verified by `pip show` commands.  
________________________________________

6. Copy & configure `.env`  
**Date:** 2025-05-07  
**Commands run:**  
```powershell
copy .env.example .env
```  
**Edits made in `.env`:  
```ini
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=rag_db
POSTGRES_PORT=5433
POSTGRES_HOST=localhost

# remaining values left as default...
OPENAI_API_KEY="sk-<your_key_here>"
```  
**Outcome:** Database & API keys configured in `.env`.  
**Notes:** 🔒 Be sure not to commit your real key.  
________________________________________

7. Launch all Docker services  
**Date:** 2025-05-07  
**Commands run:**  
```powershell
cd ..\deploy\docker
docker compose --env-file ..\..\.env up -d
docker ps
```  
**Outcome:** Postgres+pgvector and Ollama containers started.  
**Notes:** ⚠️ The Ollama container may restart repeatedly (can ignore for now).  
________________________________________

8. Clean up & start only Postgres  
**Date:** 2025-05-07  
**Commands run:**  
```powershell
docker rm -f docker-postgres-1 rag-from-scratch-db-1 rag-pgvector
docker compose --env-file ..\..\.env up -d postgres
docker ps
```  
**Outcome:** Only Postgres+pgvector service is running on port 5433.  
**Notes:** ✅ Verified with `docker ps`.  
________________________________________

8a. Enable pgvector extension  
**Date:** 2025-05-07  
**Commands run:**  
```bash
docker exec -it docker-postgres-1 psql -U postgres -d rag_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker exec -it docker-postgres-1 psql -U postgres -d rag_db -c "\dx"
```  
**Outcome:** `vector` extension installed in `rag_db`.  
**Notes:** ✅ Verified via `\dx`.  
________________________________________

9. Commit step-by-step log to Git  
**Date:** 2025-05-07  
**Commands run:**  
```bash
git add docs/STEP_BY_STEP.md
git commit -m "📒 Document Steps 1–9 in STEP_BY_STEP.md"
git push
```  
**Outcome:** Step-by-step log saved and pushed to GitHub.  
**Notes:** ✅ History is tracked and shareable.  
________________________________________

10. Tag stable database state  
**Date:** 2025-05-07  
**Commands run:**  
```bash
git checkout main
git tag -a v0.2-db-healthy -m "Postgres on 5433 up"
git push origin v0.2-db-healthy
```  
**Outcome:** Tag `v0.2-db-healthy` created for rollback.  
**Notes:** 🔖 Tags allow easy rollback to known-good state.  
________________________________________

11. Create feature branch for ingestion  
**Date:** 2025-05-07  
**Commands run:**  
```bash
git checkout -b feature/ingestion-pipeline
git push -u origin feature/ingestion-pipeline
```  
**Outcome:** Branch `feature/ingestion-pipeline` created and tracked.  
**Notes:** 🌱 Isolates new work; easy to merge or discard.  

