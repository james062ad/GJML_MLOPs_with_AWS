import boto3
from botocore.exceptions import ClientError
import os
from typing import List, Dict, Union, Callable
from functools import wraps
from server.src.models.document import RetrievedDocument  # Import the Pydantic model
from server.src.config import Settings
from fastapi import Depends
import requests
import json
from server.src.config import settings
import opik
import openai
from openai import OpenAI
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create a safe version of the opik.track decorator that won't fail if OPIK is not configured
def safe_opik_track(func: Callable) -> Callable:
    """A wrapper that makes opik.track optional - will not fail if OPIK is not configured."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Try to use OPIK tracking
            return opik.track(func)(*args, **kwargs)
        except Exception as e:
            logger.warning(f"OPIK tracking failed (this is okay in test environment): {str(e)}")
            # If OPIK fails, just call the function directly
            return func(*args, **kwargs)
    return wrapper

#----current code ----
client = OpenAI()
#----AWS code ----
# Initialize AWS Bedrock client
# bedrock_client = boto3.client(
#     service_name='bedrock-runtime',
#     region_name=settings.aws_region,
#     aws_access_key_id=settings.aws_access_key_id,
#     aws_secret_access_key=settings.aws_secret_access_key,
#     aws_session_token=settings.aws_session_token
# )

@safe_opik_track
def call_llm(prompt: str) -> Union[Dict, None]:
    """Call OpenAI's API to generate a response."""
    #----current code ----
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
    #----AWS code ----
    # try:
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
    #     # Adjust this part based on the actual response format from Bedrock
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
        logger.error(f"Error calling LLM: {str(e)}")
        return None  # TODO: error handling
    #----AWS code ----
    # except ClientError as e:
    #     print(f"Error calling AWS Bedrock API: {e}")
    #     return None  # TODO: error handling

@safe_opik_track
async def generate_response(
    query: str,
    chunks: List[Dict],
    max_tokens: int = 200,
    temperature: float = 0.7,
) -> Dict:  # str:
    """
    Generate a response using an Ollama endpoint running locally, t
    his will be changed to allow for Bedrock later.

    Args:
        query (str): The user query.
        context (List[Dict]): The list of documents retrieved from the retrieval service.
        max_tokens (int): The maximum number of tokens to generate in the response.
        temperature (float): Sampling temperature for the model.
    """
    #----current code ----
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
    #----AWS code ----
    # # The prompt format remains the same for Bedrock
    # QUERY_PROMPT = """
    # You are a helpful AI language assistant, please use the following context to answer the query. Answer in English.
    # Context: {context}
    # Query: {query}
    # Answer:
    # """
    # # Concatenate documents' summaries as the context for generation
    # context = "\n".join([chunk["chunk"] for chunk in chunks])
    # prompt = QUERY_PROMPT.format(context=context, query=query)
    # print(f"calling Bedrock API...")
    # response = call_llm(prompt)
    # print(f"generate_response returning {response}")
    # return response