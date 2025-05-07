# Step-by-Step Implementation Log

## Step 0 – Fork repo
**Date:** 2025-05-07  
**Action:** Clicked “Fork” on skok007/MLOPs_with_AWS into my account and renamed the fork to `GJML_MLOPs_with_AWS`.  
**Outcome:** New repo `github.com/james062ad/GJML_MLOPs_with_AWS` created.

## Step 1 – Clone repo
**Date:** 2025-05-07  
**Command:** `git clone https://github.com/james062ad/GJML_MLOPs_with_AWS.git`  
**Outcome:** Repo cloned successfully; files visible (`README.md`, `rag-app/`, `docker-compose.yml`, etc.).
## Step 2 – Create docs & screenshots folders  
**Date:** 2025-05-07  
**Command(s):**  
```powershell
mkdir docs
mkdir docs\screenshots
## Step 3 – Install Python dependencies  
**Date:** 2025-05-07  
**Command(s):**  
```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install --upgrade pip
pip install -r requirements.txt
## Step 3a – Install missing dependencies  
**Date:** 2025-05-07  
**Command:**  
```powershell
pip install openai boto3 streamlit


