#!/bin/bash

# refresh-session.sh
# Re-assumes the Bedrock role and exports temporary credentials

# Config
AWS_REGION="eu-west-2"
ROLE_NAME="Bedrock-Dev-FullAccess-Role"

# Get your AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

# Assume role
echo "🔄 Assuming role..."
SESSION_OUTPUT=$(aws sts assume-role \
  --role-arn arn:aws:iam::$AWS_ACCOUNT_ID:role/$ROLE_NAME \
  --role-session-name CLI-Session)

# Export credentials
export AWS_ACCESS_KEY_ID=$(echo "$SESSION_OUTPUT" | jq -r '.Credentials.AccessKeyId')
export AWS_SECRET_ACCESS_KEY=$(echo "$SESSION_OUTPUT" | jq -r '.Credentials.SecretAccessKey')
export AWS_SESSION_TOKEN=$(echo "$SESSION_OUTPUT" | jq -r '.Credentials.SessionToken')

# Confirm identity
echo "✅ Temporary credentials exported."
aws sts get-caller-identity