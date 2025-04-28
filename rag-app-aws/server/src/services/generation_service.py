import boto3
from botocore.exceptions import ClientError
import os
from typing import List, Dict, Union
from server.src.models.document import RetrievedDocument  # Import the Pydantic model
from fastapi import Depends
import requests
import json
import openai
from openai import OpenAI
from server.src.config import get_settings  # ✅ Correct lazy loading

# Conditional import for opik to allow bypassing in tests
try:
    import opik
    OPIK_AVAILABLE = True
except ImportError:
    OPIK_AVAILABLE = False
    # Create a dummy decorator for when opik is not available
    class DummyOpik:
        @staticmethod
        def track(func):
            return func
    opik = DummyOpik()

# ----current code ----
client = OpenAI()

# ----AWS code ----
# No global settings or bedrock_client instantiation at import time!


@opik.track  # TODO: test if this works with async methods? I think it will.
def call_llm(prompt: str) -> Union[Dict, None]:
    """Call OpenAI's API to generate a response."""
    settings = get_settings()  # ✅ Load settings dynamically at runtime
    # ----current code ----
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,  # Ensure this model is defined in settings
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            top_p=settings.top_p,
        )

        print("Successfully generated response")
        data = {"response": response.choices[0].message.content}
        data["response_tokens_per_second"] = (
            (response.usage.total_tokens / response.usage.completion_tokens)
            if hasattr(response, "usage")
            else None
        )
        print(f"call_llm returning {data}")
        print(f"data.response = {data['response']}")
        return data

    # ----AWS code ----
    # try:
    #     settings = get_settings()  # ✅ Load settings inside try block
    #
    #     # Initialize Bedrock client dynamically
    #     bedrock_client = boto3.client(
    #         service_name='bedrock-runtime',
    #         region_name=settings.aws_region,
    #         aws_access_key_id=settings.aws_access_key_id.get_secret_value(),
    #         aws_secret_access_key=settings.aws_secret_access_key.get_secret_value(),
    #         aws_session_token=settings.aws_session_token.get_secret_value() if settings.aws_session_token else None,
    #     )
    #
    #     # Prepare the request body for Bedrock
    #     request_body = {
    #         "prompt": prompt,
    #         "max_tokens": settings.max_tokens,
    #         "temperature": settings.temperature,
    #         "top_p": settings.top_p,
    #     }
    #
    #     # Call Bedrock API
    #     response = bedrock_client.invoke_model(
    #         modelId=settings.bedrock_model_id,
    #         body=json.dumps(request_body)
    #     )
    #
    #     # Parse the response
    #     response_body = json.loads(response.get('body').read())
    #
    #     print("Successfully generated response from Bedrock")
    #     data = {"response": response_body.get('completion')}
    #
    #     # Note: Bedrock might not provide token usage information in the same format as OpenAI
    #     if 'usage' in response_body:
    #         data["response_tokens_per_second"] = (
    #             (response_body['usage']['total_tokens'] / response_body['usage']['completion_tokens'])
    #             if 'total_tokens' in response_body['usage'] and 'completion_tokens' in response_body['usage']
    #             else None
    #         )
    #
    #     print(f"call_llm returning {data}")
    #     print(f"data.response = {data['response']}")
    #     return data

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None  # TODO: error handling

    # ----AWS code ----
    # except ClientError as e:
    #     print(f"Error calling AWS Bedrock API: {e}")
    #     return None  # TODO: error handling


@opik.track
async def generate_response(
    query: str,
    chunks: List[Dict],
    max_tokens: int = 200,
    temperature: float = 0.7,
) -> Dict:
    """
    Generate a response using an Ollama endpoint running locally,
    this will be changed to allow for Bedrock later.

    Args:
        query (str): The user query.
        chunks (List[Dict]): The list of documents retrieved from the retrieval service.
        max_tokens (int): The maximum number of tokens to generate in the response.
        temperature (float): Sampling temperature for the model.
    """
    # ----current code ----
    QUERY_PROMPT = """
    You are a helpful AI language assistant, please use the following context to answer the query. Answer in English.
    Context: {context}
    Query: {query}
    Answer:
    """
    # Concatenate documents' summaries as the context for generation
    context = "\n".join([chunk["text"] for chunk in chunks])
    prompt = QUERY_PROMPT.format(context=context, query=query)
    print(f"calling call_llm ...")
    response = call_llm(prompt)
    print(f"generate_response returning {response}")
    return response  # now this is a dict.

    # ----AWS code ----
    # # The prompt format remains the same for Bedrock
    # QUERY_PROMPT = """
    # You are a helpful AI language assistant, please use the following context to answer the query. Answer in English.
    # Context: {context}
    # Query: {query}
    # Answer:
    # """
    # # Concatenate documents' summaries as the context for generation
    # context = "\n".join([chunk["text"] for chunk in chunks])
    # prompt = QUERY_PROMPT.format(context=context, query=query)
    # print(f"calling Bedrock API...")
    # response = call_llm(prompt)
    # print(f"generate_response returning {response}")
    # return response
