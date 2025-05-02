import json
import requests
from typing import List, Dict, Union
import opik
from server.src.config import settings

# ─────────────────────────────────────────────────────────────
# 💡 Initialize Clients per Provider (on first use)
# ─────────────────────────────────────────────────────────────

openai_client = None
bedrock_client = None
azure_endpoint = None
huggingface_url = None
cohere_api_key = None
anthropic_api_key = None
google_api_key = None

if settings.llm_provider == "openai":
    from openai import OpenAI
    openai_client = OpenAI(api_key=settings.openai_api_key)

elif settings.llm_provider == "bedrock":
    import boto3
    bedrock_client = boto3.client(
        "bedrock-runtime", region_name=settings.aws_region)

elif settings.llm_provider == "azure":
    azure_endpoint = settings.azure_endpoint

elif settings.llm_provider == "huggingface":
    huggingface_url = "https://api-inference.huggingface.co/models/" + \
        settings.huggingface_model

elif settings.llm_provider == "cohere":
    cohere_api_key = settings.cohere_api_key

elif settings.llm_provider == "anthropic":
    anthropic_api_key = settings.anthropic_api_key

elif settings.llm_provider == "google":
    google_api_key = settings.google_api_key

# ─────────────────────────────────────────────────────────────
# 🤖 call_llm: Dispatch to correct backend
# ─────────────────────────────────────────────────────────────


@opik.track
def call_llm(prompt: str) -> Union[Dict[str, str], None]:
    try:
        # ─── 1. OpenAI ─────────────────────────────────────────────────────
        if settings.llm_provider == "openai":
            response = openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                top_p=settings.top_p
            )
            return {"response": response.choices[0].message.content}

        # ─── 2. AWS Bedrock ────────────────────────────────────────────────
        elif settings.llm_provider == "bedrock":
            body = json.dumps({
                "prompt": prompt,
                "max_tokens_to_sample": settings.max_tokens,
                "temperature": settings.temperature,
                "top_p": settings.top_p
            })
            response = bedrock_client.invoke_model(
                modelId=settings.bedrock_model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            result = json.loads(response["body"].read())
            return {"response": result.get("completion", "")}

        # ─── 3. Ollama (local) ─────────────────────────────────────────────
        elif settings.llm_provider == "ollama":
            response = requests.post(
                f"{settings.ollama_url}/api/generate",
                json={"model": settings.ollama_model, "prompt": prompt}
            )
            result = response.json()
            return {"response": result.get("response", "")}

        # ─── 4. HuggingFace ────────────────────────────────────────────────
        elif settings.llm_provider == "huggingface":
            headers = {
                "Authorization": f"Bearer {settings.huggingface_api_key}"}
            response = requests.post(
                huggingface_url,
                headers=headers,
                json={"inputs": prompt}
            )
            result = response.json()
            return {"response": result[0]["generated_text"] if isinstance(result, list) else result.get("generated_text", "")}

        # ─── 5. Cohere ─────────────────────────────────────────────────────
        elif settings.llm_provider == "cohere":
            response = requests.post(
                "https://api.cohere.ai/v1/generate",
                headers={
                    "Authorization": f"Bearer {cohere_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.cohere_model,
                    "prompt": prompt,
                    "max_tokens": settings.max_tokens,
                    "temperature": settings.temperature,
                    "p": settings.top_p
                }
            )
            result = response.json()
            return {"response": result.get("text", "")}

        # ─── 6. Anthropic ──────────────────────────────────────────────────
        elif settings.llm_provider == "anthropic":
            response = requests.post(
                "https://api.anthropic.com/v1/complete",
                headers={
                    "x-api-key": anthropic_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt,
                    "model": settings.anthropic_model,
                    "max_tokens_to_sample": settings.max_tokens,
                    "temperature": settings.temperature
                }
            )
            result = response.json()
            return {"response": result.get("completion", "")}

        # ─── 7. Azure OpenAI ───────────────────────────────────────────────
        elif settings.llm_provider == "azure":
            response = requests.post(
                f"{azure_endpoint}/openai/deployments/{settings.azure_deployment_name}/completions?api-version=2023-05-15",
                headers={
                    "api-key": settings.azure_openai_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt,
                    "max_tokens": settings.max_tokens,
                    "temperature": settings.temperature,
                    "top_p": settings.top_p
                }
            )
            result = response.json()
            return {"response": result["choices"][0]["text"]}

        # ─── 8. Google PaLM ────────────────────────────────────────────────
        elif settings.llm_provider == "google":
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta2/models/{settings.google_model}:generateText?key={google_api_key}",
                headers={"Content-Type": "application/json"},
                json={"prompt": {"text": prompt},
                      "temperature": settings.temperature}
            )
            result = response.json()
            return {"response": result["candidates"][0]["output"]}

        # ─── Fallback ──────────────────────────────────────────────────────
        else:
            raise ValueError(
                f"Unsupported LLM_PROVIDER: {settings.llm_provider}")

    except Exception as e:
        print(f"[call_llm] Error: {e}")
        return {"response": f"⚠️ Error: {e}"}

# ─────────────────────────────────────────────────────────────
# 🔄 generate_response: Main RAG generation logic
# ─────────────────────────────────────────────────────────────


@opik.track
async def generate_response(
    query: str,
    chunks: List[Dict],
    max_tokens: int = 200,
    temperature: float = 0.7,
) -> Dict:
    QUERY_PROMPT = """You are a helpful AI assistant. Use the following context to answer the user's question.
    Context: {context}
    Question: {query}
    Answer:"""

    context = "\n".join([chunk["text"] for chunk in chunks])
    prompt = QUERY_PROMPT.format(context=context, query=query)

    print(f"[generate_response] Provider: {settings.llm_provider}")
    return call_llm(prompt)
