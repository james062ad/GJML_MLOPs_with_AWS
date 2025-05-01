# AWS Bedrock Setup Guide

## Overview

This document provides a comprehensive guide for setting up AWS Bedrock for use with the RAG (Retrieval-Augmented Generation) project. AWS Bedrock will replace OpenAI as the language model provider for the generation service in the RAG implementation.

## Objectives

1. Set up access to AWS Bedrock, enabling API calls through the AWS CLI
2. Configure necessary IAM roles and permissions
3. Enable access to required foundation models
4. Prepare for integration with the RAG application

## Setup Steps

### 1. AWS Account Setup

- Create an AWS account if you don't already have one
- Set up a budget alert (recommended $1/day) to avoid unexpected charges

### 2. IAM Role Configuration

1. Go to IAM in the AWS console
2. Create a role called "Bedrock-Dev-FullAccess-Role"
3. Select 'AWS Account' as the trusted entity
4. Select your own account
5. Add permissions for:
   - Full access to Bedrock
   - ElasticContainerRegistry
   - ECS
   - EC2
   - CloudWatch (v2)
   - CloudFormation
   - AmazonS3
   - AWSLambdaBasicExecutionRole

### 3. IAM User Creation

- Create a user called "cli-access-user" in the IAM center

### 4. AWS CLI Configuration

1. Install AWS CLI if not already installed
2. Run `aws configure` and enter your credentials
3. Test configuration with `aws sts get-caller-identity`

### 5. Bedrock Access Policy Creation

1. Create a policy called "BedrockAccessPolicy" with permissions for:
   - bedrock:InvokeModel
   - bedrock:ListFoundationModels
   - bedrock:ListCustomModels

### 6. Role Assumption for CLI Use

1. Use the `aws sts assume-role` command to get temporary credentials:
   ```bash
   aws sts assume-role \
       --role-arn arn:aws:iam::<your-account-id>:role/Bedrock-Dev-FullAccess-Role \
       --role-session-name CLI-Session
   ```

2. Export these credentials as environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=<AccessKeyId>
   export AWS_SECRET_ACCESS_KEY=<SecretAccessKey>
   export AWS_SESSION_TOKEN=<SessionToken>
   ```

### 7. Bedrock Access Testing

- Run the following command to confirm access:
  ```bash
  aws bedrock list-foundation-models --region <your-region>
  ```

### 8. Model Access Enablement

- Enable at minimum:
  - AWS Titan G1 - Express
  - Titan Text Embeddings V2 models

### 9. Optional: Secrets Management

- Use AWS Secrets Manager for production environments

## Automated Setup

The project includes a script called `setup-aws-bedrock.sh` that can automate many of these steps. This script:

1. Creates the necessary IAM resources
2. Optionally stores credentials in AWS Secrets Manager
3. Tests Bedrock access

To use the script:
```bash
./setup-aws-bedrock.sh [options]
```

Options include:
- `-r, --region REGION`: AWS region (default: eu-west-2)
- `-u, --user USERNAME`: IAM user name (default: cli-access-user)
- `-p, --role ROLE_NAME`: IAM role name (default: Bedrock-Dev-FullAccess-Role)
- `-s, --secret SECRET_NAME`: Secret name for storing credentials
- `-k, --key-file KEY_FILE`: File to store access keys
- `-a, --account-id ACCOUNT_ID`: AWS account ID
- `--store-secret`: Store credentials in AWS Secrets Manager
- `--skip-policies`: Skip creating policies (use existing ones)

## Code Changes Required

After completing the AWS setup, you'll need to modify the following files to integrate AWS Bedrock with your RAG application:

### 1. Update `rag-app/server/src/services/generation_service.py`

This file contains the current OpenAI implementation and needs to be updated to use AWS Bedrock:

1. Comment out the OpenAI client initialization:
   ```python
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
   ```

2. Replace the `call_llm` function with the AWS Bedrock implementation:
   ```python
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
   ```

3. Update the error handling:
   ```python
   #----current code ----
   except Exception as e:
       print(f"Error calling OpenAI API: {e}")
       return None  # TODO: error handling
   #----AWS code ----
   # except ClientError as e:
   #     print(f"Error calling AWS Bedrock API: {e}")
   #     return None  # TODO: error handling
   ```

4. Update the `generate_response` function:
   ```python
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
   # context = "\n".join([chunk["text"] for chunk in chunks])
   # prompt = QUERY_PROMPT.format(context=context, query=query)
   # print(f"calling Bedrock API...")
   # response = call_llm(prompt)
   # print(f"generate_response returning {response}")
   # return response
   ```

### 2. Update `rag-app/server/src/config.py`

Add AWS Bedrock configuration settings to the Settings class:

```python
#----current code ----
# OpenAI config
openai_model: str = Field(..., env="OPENAI_MODEL")
openai_api_key: str = Field(..., env="OPENAI_API_KEY")
#----AWS code ----
# AWS Bedrock config
# aws_region: str = Field(..., env="AWS_REGION")
# aws_access_key_id: str = Field(..., env="AWS_ACCESS_KEY_ID")
# aws_secret_access_key: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
# aws_session_token: str = Field(None, env="AWS_SESSION_TOKEN")  # Optional, for temporary credentials
# bedrock_model_id: str = Field(..., env="BEDROCK_MODEL_ID")  # e.g., "amazon.titan-text-express-v1"
```

### 3. Update `rag-app/server/config/rag.yaml`

Update the generation configuration to use AWS Bedrock:

```yaml
#----current code ----
generation:
  model: "tinyllama"
  #max_tokens: 150
  temperature: 0.7
#----AWS code ----
# generation:
#   model: "bedrock"  # Use "bedrock" instead of "tinyllama" or "openai"
#   bedrock_model_id: "amazon.titan-text-express-v1"  # Specific Bedrock model ID
#   #max_tokens: 150
#   temperature: 0.7
#   aws_region: "eu-west-2"  # AWS region where Bedrock is available
```

### 4. Update `rag-app/server/src/config_loader.py`

Enhance the ConfigLoader class to handle AWS Bedrock configuration:

```python
#----current code ----
class ConfigLoader:
    _config = None

    @classmethod
    def load_config(cls, config_name: str):
        """
        Loads the configuration file from the config/ directory.
        This method caches the configuration to avoid reloading multiple times.
        """
        if cls._config is None:
            # Determine the base path of the configuration directory
            config_path = os.path.join(
                os.path.dirname(__file__), "../config", f"{config_name}.yaml"
            )

            # Load the YAML config file
            with open(config_path, "r") as file:
                cls._config = yaml.safe_load(file)

        return cls._config

    @classmethod
    def get_config_value(cls, key: str, default: Any = None) -> Optional[Any]:
        """
        Retrieve a specific config value from the loaded configuration.
        """
        if cls._config is None:
            raise ValueError("Configuration not loaded. Please call load_config first.")

        return cls._config.get(key, default)

#----AWS code ----
# class ConfigLoader:
#     _config = None
# 
#     @classmethod
#     def load_config(cls, config_name: str):
#         """
#         Loads the configuration file from the config/ directory and handles Bedrock settings.
#         """
#         if cls._config is None:
#             config_path = os.path.join(
#                 os.path.dirname(__file__), "../config", f"{config_name}.yaml"
#             )
# 
#             with open(config_path, "r") as file:
#                 cls._config = yaml.safe_load(file)
# 
#             # Handle Bedrock configuration
#             if cls._config.get("generation", {}).get("model") == "bedrock":
#                 from server.src.config import settings
#                 gen_config = cls._config.get("generation", {})
#                 
#                 # Update Bedrock settings
#                 if hasattr(settings, "bedrock_model_id"):
#                     settings.bedrock_model_id = gen_config.get("bedrock_model_id")
#                 if hasattr(settings, "aws_region"):
#                     settings.aws_region = gen_config.get("aws_region")
# 
#         return cls._config
# 
#     @classmethod
#     def get_config_value(cls, key: str, default: Any = None) -> Optional[Any]:
#         """
#         Retrieve config values with special handling for Bedrock settings.
#         """
#         if cls._config is None:
#             raise ValueError("Configuration not loaded. Please call load_config first.")
# 
#         # Handle Bedrock-specific keys
#         if key in ["bedrock_model_id", "aws_region"]:
#             return cls._config.get("generation", {}).get(key, default)
#         elif key == "model_type":
#             return cls._config.get("generation", {}).get("model", default)
# 
#         return cls._config.get(key, default)
# 
#     @classmethod
#     def is_using_bedrock(cls) -> bool:
#         """Check if AWS Bedrock is enabled in config."""
#         if cls._config is None:
#             raise ValueError("Configuration not loaded. Please call load_config first.")
#         return cls._config.get("generation", {}).get("model") == "bedrock"
```

## Implementation Steps

1. Complete the AWS setup steps in this guide
2. Update your .env file with the new AWS credentials:
   ```
   AWS_REGION=eu-west-2
   AWS_ACCESS_KEY_ID=your_access_key_id
   AWS_SECRET_ACCESS_KEY=your_secret_access_key
   AWS_SESSION_TOKEN=your_session_token  # If using temporary credentials
   BEDROCK_MODEL_ID=amazon.titan-text-express-v1
   ```
3. For each file mentioned above:
   - Comment out the current code sections (marked with `#----current code ----`)
   - Uncomment the AWS code sections (marked with `#----AWS code ----`)
4. Test the integration with AWS Bedrock

## Troubleshooting

### Common Issues

1. **Permission Errors**:
   - Verify IAM role and policy configurations
   - Check that the role has been properly assumed

2. **Model Access Issues**:
   - Ensure models are enabled in the AWS console
   - Verify region settings match where models are available

3. **Credential Problems**:
   - Check that credentials are properly exported
   - Verify session tokens haven't expired

## Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)
- [IAM Roles for AWS Services](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_aws-service.html)
- [AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) 