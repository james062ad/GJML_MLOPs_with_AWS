import json
import requests
from typing import List, Dict, Union
import opik
from server.src.config import settings


# ─────────────────────────────────────────────────────────────
# 🔁 PROVIDER-SPECIFIC CLIENT SETUP
# ─────────────────────────────────────────────────────────────

if settings.llm_provider == 'openai':
    from openai import OpenAI
    openai_client = OpenAI(api_key=settings.openai_api_key)

elif settings.llm_provider == 'bedrock':
    import boto3
    bedrock_client = boto3.client(
        service_name='bedrock-runtime',
        region_name=settings.aws_region
    )

elif settings.llm_provider == 'ollama':
    import requests  # already imported, just kept for clarity

# Future placeholders (do nothing yet but structure is ready)
# elif settings.llm_provider == 'huggingface':
# elif settings.llm_provider == 'azure':
# elif settings.llm_provider == 'anthropic':
# etc.

# ─────────────────────────────────────────────────────────────
# 🤖 call_llm: Unified Model Dispatcher
# ─────────────────────────────────────────────────────────────

@opik.track
def call_llm(prompt: str) -> Union[Dict, None]:
    """
    Call the appropriate LLM backend based on the LLM_PROVIDER setting in the environment.

    Returns:
        dict: { "response": "<string>" }
    """
    try:
        if settings.llm_provider == 'openai':
            # 🔵 OpenAI GPT-3.5 / GPT-4
            response = openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                top_p=settings.top_p
            )
            return {"response": response.choices[0].message.content}

        elif settings.llm_provider == 'bedrock':
            # 🟠 AWS Bedrock (Anthropic Claude, Titan, etc.)
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
            # 🐴 Ollama running locally (e.g. LLaMA2, Mistral)
            response = requests.post(
                f"{settings.ollama_url}/api/generate",
                json={"model": settings.ollama_model, "prompt": prompt}
            )
            result = response.json()
            return {"response": result.get("response", "")}

        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")

    except Exception as e:
        print(f"[call_llm] Error with provider '{settings.llm_provider}': {e}")
        return None

# ─────────────────────────────────────────────────────────────
# 🧠 generate_response: RAG prompt generator
# ─────────────────────────────────────────────────────────────

@opik.track
async def generate_response(
    query: str,
    chunks: List[Dict],
    max_tokens: int = 200,
    temperature: float = 0.7,
) -> Dict:
    """
    Generate a completion using retrieved documents + query context.

    Args:
        query (str): The user's original query.
        chunks (List[Dict]): Contextual chunks retrieved by vector store.
        max_tokens (int): Max tokens to generate.
        temperature (float): Sampling temperature.

    Returns:
        Dict: The LLM response in standardized format.
    """

    # Build the unified prompt
    QUERY_PROMPT = """You are a helpful AI assistant. Use the following context to answer the user's question.
    Context: {context}
    Question: {query}
    Answer:"""

    context = "\n".join([chunk["text"] for chunk in chunks])
    prompt = QUERY_PROMPT.format(context=context, query=query)

    print(f"[generate_response] Calling call_llm with provider: {settings.llm_provider}")
    response = call_llm(prompt)
    print(f"[generate_response] Response: {response}")
    return response
