# ✅ Enhanced RAG App: Change Report & Walkthrough

## 🧠 Project Enhancement Overview

**Objective:**  
Transform the original [oxford-genai-llmops-project](https://github.com/AndyMc629/oxford-genai-llmops-project) into a robust, multi-provider Retrieval-Augmented Generation (RAG) application with an improved user interface and flexible architecture.

**Key Enhancements:**

1. **Multi-Provider Support:**  
   Integrated support for:
   - OpenAI
   - Amazon Bedrock
   - Google Vertex AI
   - Cohere
   - HuggingFace
   - Ollama (local)

2. **Dynamic Embedding Handling:**  
   Auto-detects embedding dimensions, ensuring compatibility.

3. **Streamlit Interface Overhaul:**  
   Improved controls, user feedback, and model switching.

4. **Secure Credential Handling:**  
   Includes AWS STS via `runtime_credentials.py`.

5. **Modularization & Error Handling:**  
   Cleaner logic, better separation of concerns.

---

## 📁 Detailed File-by-File Changes

### 1. `streamlit_app.py` – Enhanced User Interface

- Dropdown for model combinations
- Parameter sliders for temperature, top_k, max_tokens, etc.
- Vector DB rebuild with real-time status
- Clear chat and timestamped messages
- Code modularization with `apply_custom_css`, `display_sidebar`, etc.

### 2. `config.py` – Flexible Configuration Management

- Refactored with Pydantic `Field(...)` and `SecretStr`
- Added config keys for all providers
- Supports secure token retrieval and fallbacks

### 3. `generation_service.py` – Unified LLM Calling

- Provider dispatch logic added:
  ```python
  if settings.llm_provider == "openai":
      ...
  elif settings.llm_provider == "bedrock":
      ...
  ```
- Consistent prompt format
- Try/except around API calls
- Added `response_tokens_per_second` where available

### 4. `retrieval_service.py` – Dynamic Embedding

- Uses selected provider to embed query:
  ```python
  def embed_query(query):
      if settings.embedding_provider == "bedrock":
          ...
  ```
- Removed hardcoded dimensions
- Query embedding dynamically matched with DB vector dimension

### 5. `ingestion_service.py` – Provider-Aware Ingestion

- `detect_embedding_dim()` infers dim from provider
- `write_pgvector_sql()` aligns DB table to embedding dim
- Ingestion now calls `generate_embeddings()` with the selected provider logic

### 6. `runtime_credentials.py` – AWS STS Support

- Automates generation of session tokens
- Can be used for refreshing credentials every hour
- Used by `get_bedrock_client()` for safe AWS Bedrock calls

### 7. `bedrock_client_factory.py` – Shared Bedrock Session Builder

- Called by generation and ingestion
- Uses AWS env vars or temp credentials
- Caches Boto3 client instance

---

## ✅ Summary

With these changes, the repo now supports:
- Multi-model workflows
- Full vector DB management
- Real-time RAG interaction
- Secure credential flow

Perfect for: demonstrations, experimentation, or as a backbone for further cloud deployment.