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

## Integration with RAG Project

### What's Being Replaced

The RAG implementation currently uses:
1. **OpenAI's API** for the generation service
2. **SentenceTransformer** for embedding generation

### How AWS Bedrock Fits In

AWS Bedrock will primarily replace OpenAI for the response generation step in the RAG pipeline:

1. **Document Processing**: Breaking documents into chunks and creating embeddings
2. **Query Processing**: Converting user queries to embeddings and finding relevant documents
3. **Response Generation**: Using AWS Bedrock models instead of OpenAI to generate answers

### Benefits of Using AWS Bedrock

1. **Cost Management**: Potentially more cost-effective than OpenAI
2. **Integration**: Better integration with other AWS services
3. **Flexibility**: Access to multiple models with different capabilities
4. **Enterprise Features**: Better security and compliance features

## Next Steps After Setup

1. Modify the generation service code to use AWS Bedrock instead of OpenAI
2. Update configuration to include AWS Bedrock settings
3. Test the system with the new model provider
4. Consider implementing AWS Bedrock embeddings as an alternative to SentenceTransformer

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