from server.src.services.generation_service import call_llm
from typing import Union, Dict
import opik
from server.src.config import settings


@opik.track
def expand_query(query: str) -> Union[Dict[str, str], None]:
    """
    Expands a user query using the configured LLM provider.
    Also logs trace info to Opik for visibility.

    Returns:
        dict with:
        - original_query
        - expanded_query
        - provider
        - prompt
    """

    # Construct the prompt
    prompt = f"""
    Expand the following query using synonyms and related phrases.
    Make it more expressive to improve semantic retrieval performance.

    Query: {query}
    Expanded Query:
    """

    # Call the LLM backend (OpenAI, Bedrock, etc.)
    result = call_llm(prompt)

    if result and "response" in result:
        expanded = result["response"].strip().replace('"', "")
        provider = settings.llm_provider

        # ✅ Send metadata to Opik as trace tags
        opik.set_tags({
            "llm_provider": provider,
            "query.original": query,
            "query.expanded": expanded,
            "query.prompt_used": prompt.strip()
        })

        return {
            "original_query": query,
            "expanded_query": expanded,
            "provider": provider,
            "prompt": prompt.strip()
        }

    # On failure
    opik.set_tags({"expansion_status": "failed",
                  "llm_provider": settings.llm_provider})
    return None
