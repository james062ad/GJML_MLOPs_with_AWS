
# Critical Changes Required for oxford-genai-llmops-project

This document outlines the critical changes needed to make the [oxford-genai-llmops-project](https://github.com/AndyMc629/oxford-genai-llmops-project) repository work properly. These changes address compatibility issues, dependency problems, configuration errors, and expand the system to support multiple embedding and generation model providers.

## Summary of Changes

The following key changes were implemented to improve the repository:

1. **Certificate Configuration** – Enable Zscaler and custom certs.
2. **PostgreSQL Configuration** – Use pgvector with init and health checks.
3. **CI/CD Pipeline** – Add GitHub Actions CI.
4. **Streamlit App Enhancements** – Enhanced styling, controls, and model rebuild support.
5. **Multi-Model Support** – Add general support for OpenAI, Bedrock, Google, Cohere, HuggingFace, and Ollama.

---

## 1. Certificate Configuration

_(Unchanged from original. See previous version for full detail.)_

---

## 2. PostgreSQL Configuration

_(Unchanged from original. Includes init scripts and vector extensions.)_

---

## 3. CI/CD Pipeline

_(Unchanged. GitHub Actions integrated with Poetry, Postgres, and Pytest.)_

---

## 4. Streamlit App Improvements (Expanded)

### 4.1 Unified Model Selection

Users can now select from:
- OpenAI (LLM and/or embeddings)
- Bedrock (LLM and/or embeddings)
- Google
- Cohere
- HuggingFace
- Ollama

```python
model_mode = st.selectbox(
    "Model Configuration",
    options=[
        "OpenAI + SentenceTransformer",
        "OpenAI (Embedding + LLM)",
        "Bedrock",
        "Cohere",
        "Ollama",
        "Google PaLM"
    ],
)
```

### 4.2 Rebuild Vector DB Integration

A full vector rebuild pipeline is triggered from the sidebar when provider changes:
```python
response = requests.post("http://localhost:8000/rebuild", params={
    "json_dir": "./papers-downloads",
    "output_file": "init/processed_papers.json",
    "chunk_size": st.session_state["chunk_size"],
    "overlap": st.session_state["overlap"],
})
```

### 4.3 Advanced Model Controls

User parameters for:
- `Top K`
- `Max Tokens`
- `Temperature`
- `Chunk Size`
- `Overlap`

```python
st.session_state["top_k"] = st.slider("Top K", 1, 10, 5)
st.session_state["max_tokens"] = st.slider("Max Tokens", 50, 1000, 300)
st.session_state["temperature"] = st.slider("Temperature", 0.0, 1.0, 0.7)
```

### 4.4 Status Indicators and Spinner

Feedback when models are switched, and when DB is stale:
```python
if not st.session_state.get("db_is_fresh"):
    st.warning("⚠️ Please rebuild the vector database...")
```

---

## 5. Multi-Model Provider Support

### 5.1 `.env` Additions

```env
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=sentence-transformer

OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...
AWS_REGION=eu-west-2
BEDROCK_MODEL_ID=amazon.titan-text-express-v1
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0

GOOGLE_API_KEY=...
GOOGLE_MODEL=gemini-1.5-pro
GOOGLE_EMBEDDING_MODEL=text-embedding-004
```

### 5.2 `config.py`

```python
llm_provider: str = Field(..., env="LLM_PROVIDER")
embedding_provider: str = Field(..., env="EMBEDDING_PROVIDER")
google_api_key: str = Field(..., env="GOOGLE_API_KEY")
google_embedding_model: str = Field(..., env="GOOGLE_EMBEDDING_MODEL")
```

### 5.3 `generation_service.py`

```python
elif settings.llm_provider == "google":
    url = f"https://generativelanguage.googleapis.com/v1/models/{settings.google_model}:generateContent?key={settings.google_api_key}"
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temp,
            "topP": settings.top_p,
            "maxOutputTokens": max_t
        }
    }
    response = requests.post(url, headers=headers, json=body)
    result = response.json()
    return {
        "response": result["candidates"][0]["content"]["parts"][0]["text"],
        "response_tokens_per_second": None
    }
```

### 5.4 `ingestion_service.py` – Google Support

```python
elif provider == "google":
    url = f"https://generativelanguage.googleapis.com/v1/models/{settings.google_embedding_model}:embedContent?key={settings.google_api_key}"
    headers = {"Content-Type": "application/json"}
    body = {"content": {"parts": [{"text": example_text}]}}
    response = requests.post(url, headers=headers, json=body)
    result = response.json()
    return len(result["embedding"]["value"])
```

### 5.5 `embeddings.py`

```python
elif provider == "google":
    ...
    for chunk in text_chunks:
        body = {"content": {"parts": [{"text": chunk}]}}
        response = requests.post(url, headers=headers, json=body)
        result = response.json()
        embeddings.append(result["embedding"]["value"])
```

### 5.6 `retrieval_service.py` (Query Embed)

```python
elif provider == "google":
    ...
    body = {"content": {"parts": [{"text": query}]}}
    response = requests.post(url, headers=headers, json=body)
    return response.json()["embedding"]["value"]
```

---

This concludes the documentation of all critical changes and enhancements.
