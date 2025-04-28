#!/bin/bash

# load-bedrock-credentials.sh
# Loads AWS Bedrock CLI credentials from Secrets Manager into your current terminal session

# Settings
AWS_REGION="eu-west-2"
SECRET_NAME="bedrock-api-config"

# Check dependencies
if ! command -v aws &> /dev/null; then
  echo "❌ AWS CLI is not installed. Please install it first."
  exit 1
fi

if ! command -v jq &> /dev/null; then
  echo "❌ jq is not installed. Please install it first."
  exit 1
fi

# Fetch secret
echo "🔐 Loading credentials from Secrets Manager..."
SECRET_JSON=$(aws secretsmanager get-secret-value \
  --secret-id "$SECRET_NAME" \
  --region "$AWS_REGION" \
  --query 'SecretString' \
  --output text)

if [[ -z "$SECRET_JSON" ]]; then
  echo "❌ Failed to retrieve secret '$SECRET_NAME'."
  exit 1
fi

# Extract keys
AWS_ACCESS_KEY_ID=$(echo "$SECRET_JSON" | jq -r '.AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY=$(echo "$SECRET_JSON" | jq -r '.AWS_SECRET_ACCESS_KEY')

# Export to environment
export AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN

echo "✅ AWS credentials loaded into your terminal session."
echo "You can now run AWS CLI commands targeting Bedrock!"

# (Optional) Show your identity to confirm
aws sts get-caller-identity