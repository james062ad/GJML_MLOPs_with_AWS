# server/src/utils/bedrock_client_factory.py

"""
Factory for creating boto3 Bedrock clients using live STS credentials.
"""
import boto3
from server.src.services.runtime_credentials import get_aws_credentials
from server.src.config import settings


def get_bedrock_client():
    creds = get_aws_credentials()
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.aws_region,
        aws_access_key_id=creds["access_key"],
        aws_secret_access_key=creds["secret_key"],
        aws_session_token=creds["session_token"]
    )
