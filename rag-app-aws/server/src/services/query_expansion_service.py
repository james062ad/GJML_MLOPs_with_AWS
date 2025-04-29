from server.src.services.generation_service import call_llm
from typing import Union
import opik


@opik.track
def expand_query(query: str) -> Union[str, None]:
    """
    Expands the query using the active LLM provider via call_llm().
    Supports OpenAI, AWS Bedrock, or Ollama depending on config.
    """
    expansion_prompt = f"""
    Expand the following query, specifically add relevant synonyms for key topics and phrases.
    Your goal is to increase the chances of a relevant retrieval from the knowledge base.

    Query: {query}
    """
    result = call_llm(expansion_prompt)
    if result and "response" in result:
        return result["response"].replace('"', "")
    return None
