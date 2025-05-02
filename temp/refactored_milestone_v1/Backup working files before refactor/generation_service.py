import json
import requests
from typing import List, Dict, Union
import opik
from server.src.config import settings
from server.src.utils.bedrock_client_factory import get_bedrock_client
from openai import OpenAI

# Initialize client placeholders
openai_client = None
bedrock_client = None
azure_endpoint = None
huggingface_url = None
cohere_api_key = None
anthropic_api_key = None
google_api_key = None

# Initialize actual clients based on provider
if settings.llm_provider == "openai":
    openai_client = OpenAI(api_key=settings.openai_api_key)
elif settings.llm_provider == "bedrock":
    bedrock_client = get_bedrock_client()
elif settings.llm_provider == "azure":
    azure_endpoint = settings.azure_endpoint
elif settings.llm_provider == "huggingface":
    huggingface_url = f"https://api-inference.huggingface.co/models/{settings.huggingface_model}"
elif settings.llm_provider == "cohere":
    cohere_api_key = settings.cohere_api_key
elif settings.llm_provider == "anthropic":
    anthropic_api_key = settings.anthropic_api_key
elif settings.llm_provider == "google":
    google_api_key = settings.google_api_key


@opik.track
def call_llm(prompt: str, temperature: float = None, max_tokens: int = None) -> Union[Dict[str, Union[str, float, None]], None]:
    temp = temperature or settings.temperature
    max_t = max_tokens or settings.max_tokens

    try:
        if settings.llm_provider == "openai":
            response = openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                max_tokens=max_t,
                top_p=settings.top_p
            )
            return {
                "response": response.choices[0].message.content,
                "response_tokens_per_second": (
                    (response.usage.total_tokens /
                     response.usage.completion_tokens)
                    if hasattr(response, "usage") else None
                )
            }

        elif settings.llm_provider == "bedrock":
            client = get_bedrock_client()

            body = json.dumps({
                "inputText": prompt,  # ✅ Titan expects "inputText"
                "textGenerationConfig": {  # ✅ Nest under textGenerationConfig
                    "maxTokenCount": max_t,     # ✅ Correct key name for Titan
                    "temperature": temp,
                    "topP": settings.top_p,
                    "stopSequences": []         # ✅ Optional, included for safety
                }
            })

            response = client.invoke_model(
                modelId=settings.bedrock_model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )

            result = json.loads(response["body"].read())
            return {
                "response": result.get("results", [{}])[0].get("outputText", ""),
                "response_tokens_per_second": None
            }
        elif settings.llm_provider == "ollama":
            response = requests.post(
                f"{settings.ollama_url}/api/generate",
                json={"model": settings.ollama_model, "prompt": prompt}
            )
            result = response.json()
            return {"response": result.get("response", ""), "response_tokens_per_second": None}

        elif settings.llm_provider == "huggingface":
            headers = {
                "Authorization": f"Bearer {settings.huggingface_api_key}"}
            response = requests.post(
                huggingface_url,
                headers=headers,
                json={"inputs": prompt}
            )
            result = response.json()
            return {"response": result[0]["generated_text"] if isinstance(result, list) else result.get("generated_text", ""), "response_tokens_per_second": None}

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
                    "max_tokens": max_t,
                    "temperature": temp,
                    "p": settings.top_p
                }
            )
            result = response.json()
            return {"response": result.get("text", ""), "response_tokens_per_second": None}

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
                    "max_tokens_to_sample": max_t,
                    "temperature": temp
                }
            )
            result = response.json()
            return {"response": result.get("completion", ""), "response_tokens_per_second": None}

        elif settings.llm_provider == "azure":
            response = requests.post(
                f"{azure_endpoint}/openai/deployments/{settings.azure_deployment_name}/completions?api-version=2023-05-15",
                headers={
                    "api-key": settings.azure_openai_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt,
                    "max_tokens": max_t,
                    "temperature": temp,
                    "top_p": settings.top_p
                }
            )
            result = response.json()
            return {"response": result["choices"][0]["text"], "response_tokens_per_second": None}

        elif settings.llm_provider == "google":
            url = f"https://generativelanguage.googleapis.com/v1/models/{settings.google_model}:generateContent?key={settings.google_api_key}"
            headers = {"Content-Type": "application/json"}
            body = {
                "contents": [
                    {
                        "parts": [{"text": prompt}]
                    }
                ],
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

        else:
            raise ValueError(
                f"Unsupported LLM_PROVIDER: {settings.llm_provider}")

    except Exception as e:
        print(f"[call_llm] Error: {e}")
        return {"response": f"⚠️ Error: {e}", "response_tokens_per_second": None}


@opik.track
def generate_response(
    query: str,
    chunks: List[Dict],
    max_tokens: int = 200,
    temperature: float = 0.7,
) -> Dict:
    context = format_context_from_chunks(chunks)
    prompt = create_prompt_with_context(query, context)
    print(f"[generate_response] Provider: {settings.llm_provider}")
    result = call_llm(prompt, temperature=temperature, max_tokens=max_tokens)
    return {
        "query": query,
        "context": context,
        "response": result["response"],
        "response_tokens_per_second": result.get("response_tokens_per_second")
    }


def format_context_from_chunks(chunks: List[Dict]) -> str:
    if not chunks:
        return "No relevant context available."

    formatted_chunks = []
    for i, chunk in enumerate(chunks, 1):
        title = chunk.get("title", "Untitled")
        content = chunk.get("chunk", "")
        formatted_chunks.append(f"Document {i} - {title}:\n{content}\n")

    return "\n".join(formatted_chunks)


def create_prompt_with_context(query: str, context: str) -> str:
    return (
        "You are a helpful AI assistant that provides information based on the "
        "following context:\n\n"
        f"{context}\n\n"
        f"User Query: {query}\n\n"
        "Please provide a comprehensive answer based on the information in the "
        "context above. If the context doesn't contain relevant information to "
        "answer the query, please say so."
    )
