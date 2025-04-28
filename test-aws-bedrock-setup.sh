#!/bin/bash

# test-aws-bedrock-setup.sh
# Script to validate AWS Bedrock setup after running setup-aws-bedrock.sh

set -e

# --- CONFIGURATION ---

AWS_REGION="eu-west-2"
USER_NAME="cli-access-user"
ROLE_NAME="Bedrock-Dev-FullAccess-Role"
POLICY_NAME="BedrockAccessPolicy"
ENV_FILE_PATH="rag-app-aws/.env"

# --- FUNCTIONS ---

handle_error() {
  echo "❌ $1"
  exit 1
}

check_command() {
  if ! command -v $1 &> /dev/null; then
    handle_error "$1 is required but not installed. Please install it first."
  fi
}

check_iam_user() {
  echo "🔍 Checking IAM user $USER_NAME..."
  if aws iam get-user --user-name "$USER_NAME" > /dev/null 2>&1; then
    echo "✅ IAM user exists."
  else
    handle_error "IAM user $USER_NAME does not exist!"
  fi
}

check_iam_role() {
  echo "🔍 Checking IAM role $ROLE_NAME..."
  if aws iam get-role --role-name "$ROLE_NAME" > /dev/null 2>&1; then
    echo "✅ IAM role exists."
  else
    handle_error "IAM role $ROLE_NAME does not exist!"
  fi
}

check_policy_exists() {
  echo "🔍 Checking IAM policy $POLICY_NAME..."
  POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text)
  if [ -z "$POLICY_ARN" ]; then
    handle_error "IAM policy $POLICY_NAME does not exist!"
  else
    echo "✅ IAM policy exists."
  fi
}

check_policy_attached_to_role() {
  echo "🔍 Checking if $POLICY_NAME is attached to $ROLE_NAME..."
  POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text)
  ATTACHED=$(aws iam list-attached-role-policies --role-name "$ROLE_NAME" --query "AttachedPolicies[?PolicyArn=='$POLICY_ARN']" --output text)
  if [ -z "$ATTACHED" ]; then
    handle_error "IAM policy $POLICY_NAME is NOT attached to $ROLE_NAME!"
  else
    echo "✅ IAM policy is attached correctly."
  fi
}

check_bedrock_access() {
  echo "🔍 Testing Bedrock API access..."
  if aws bedrock list-foundation-models --region "$AWS_REGION" > /dev/null 2>&1; then
    echo "✅ Bedrock API access is working."
  else
    handle_error "Bedrock API access failed!"
  fi
}

check_env_file() {
  echo "🔍 Checking .env file at $ENV_FILE_PATH..."
  if [ ! -f "$ENV_FILE_PATH" ]; then
    handle_error ".env file does not exist at $ENV_FILE_PATH!"
  fi

  REQUIRED_KEYS=("AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY" "AWS_SESSION_TOKEN" "AWS_REGION" "BEDROCK_MODEL_ID" "BEDROCK_EMBEDDING_MODEL_ID")
  for key in "${REQUIRED_KEYS[@]}"; do
    if ! grep -q "^$key=" "$ENV_FILE_PATH"; then
      handle_error "Missing $key in .env file!"
    fi
  done
  echo "✅ .env file contains all required AWS/Bedrock keys."
}

# --- SCRIPT EXECUTION ---

echo "🚀 Starting AWS Bedrock setup validation..."

check_command aws
check_command jq

check_iam_user
check_iam_role
check_policy_exists
check_policy_attached_to_role
check_bedrock_access
check_env_file

echo
echo "🎯✅ All checks passed! Your AWS Bedrock environment is correctly set up!"