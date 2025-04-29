import os
import json
import requests
from typing import List, Dict, Union
import opik
from server.src.config import settings

# ─────────────────────────────────────────────────────────────
# 📦 CONDITIONAL IMPORTS based on LLM_PROVIDER
# ─────────────────────────────────────────────────────────────
# We only import the relevant SDK/client depending on the model provider

if settings.llm_provider == 'openai':
    # OpenAI client
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)

elif settings.llm_provider == 'bedrock':
    # AWS Bedrock client
    import boto3
    bedrock_client = boto3.client(
        service_name='bedrock-runtime',
        region_name=settings.aws_region
    )

elif settings.llm_provider == 'ollama':
    # Ollama uses HTTP calls to localhost:11434
    import requests


# ─────────────────────────────────────────────────────────────
# 🤖 Unified LLM Call Function
# ─────────────────────────────────────────────────────────────
@opik.track
def call_llm(prompt: str) -> Union[Dict, None]:
    """
    Dispatches prompt to the correct LLM backend based on the value of settings.llm_provider.
    
    Returns a dictionary of form:
        { "response": <string> }
    """
    try:
        if settings.llm_provider == 'openai':
            # 🟢 Using OpenAI
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                top_p=settings.top_p
            )
            return {"response": response.choices[0].message.content}

        elif settings.llm_provider == 'bedrock':
            # 🟠 Using AWS Bedrock
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
            response_body = json.loads(response['body'].read())
            return {"response": response_body.get("completion", "")}

        elif settings.llm_provider == 'ollama':
            # 🐴 Using Ollama (local LLaMA2 or similar)
            response = requests.post(
                f"{settings.ollama_url}/api/generate",
                json={"model": settings.ollama_model, "prompt": prompt}
            )
            result = response.json()
            return {"response": result.get("response", "")}

        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")

    except Exception as e:
        print(f"Error in call_llm for provider '{settings.llm_provider}': {e}")
        return None


# ─────────────────────────────────────────────────────────────
# 🧠 Main RAG Generation Function
# ─────────────────────────────────────────────────────────────
@opik.track
async def generate_response(
    query: str,
    chunks: List[Dict],
    max_tokens: int = 200,
    temperature: float = 0.7,
) -> Dict:
    """
    Uses call_llm() to generate a response to a user query based on retrieved context chunks.
    """
    QUERY_PROMPT = """
    You are a helpful AI language assistant. Use the context below to answer the query:
    Context: {context}
    Query: {query}
    Answer:
    """
    # Combine the retrieved documents into one input string
    context = "\n".join([chunk["text"] for chunk in chunks])
    prompt = QUERY_PROMPT.format(context=context, query=query)

    print(f"[generate_response] Calling call_llm() with prompt using provider: {settings.llm_provider}")
    return call_llm(prompt)
