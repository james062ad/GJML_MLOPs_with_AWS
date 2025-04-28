#!/bin/bash

# Config
AWS_REGION="eu-west-2"
SECRET_NAME="bedrock-api-config"

echo "🔐 Retrieving credentials from AWS Secrets Manager..."

# Get secret value and parse it
SECRET_JSON=$(aws secretsmanager get-secret-value \
  --secret-id "$SECRET_NAME" \
  --region "$AWS_REGION" \
  --query 'SecretString' \
  --output text)

if [[ -z "$SECRET_JSON" ]]; then
  echo "❌ Failed to retrieve secret '$SECRET_NAME'."
  exit 1
fi

# Export credentials as environment variables
export AWS_ACCESS_KEY_ID=$(echo "$SECRET_JSON" | jq -r '.AWS_ACCESS_KEY_ID')
export AWS_SECRET_ACCESS_KEY=$(echo "$SECRET_JSON" | jq -r '.AWS_SECRET_ACCESS_KEY')
unset AWS_SESSION_TOKEN  # Static creds don't use this

echo "✅ AWS credentials loaded into your environment."

# Test access
echo "🧪 Verifying identity..."
aws sts get-caller-identity