
""" Runtime Credential Store: Supplies credentials to boto3 clients. """
from .aws_refresh_service import CredentialStore

def get_aws_credentials():
    return CredentialStore.get_credentials()
