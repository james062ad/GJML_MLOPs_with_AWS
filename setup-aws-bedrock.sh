#!/bin/bash

# setup-aws-bedrock.sh
# This script sets up AWS Bedrock access by creating the necessary IAM resources
# and optionally stores the credentials in AWS Secrets Manager.
#
# Usage:
#   ./setup-aws-bedrock.sh [options]
#
# Options:
#   -h, --help                 Display this help message
#   -r, --region REGION        AWS region (default: eu-west-2)
#   -u, --user USERNAME        IAM user name (default: cli-access-user)
#   -p, --role ROLE_NAME       IAM role name (default: Bedrock-Dev-FullAccess-Role)
#   -s, --secret SECRET_NAME   Secret name for storing credentials (default: bedrock-api-config)
#   -k, --key-file KEY_FILE    File to store access keys (default: cli-access-user-keys.json)
#   -a, --account-id ACCOUNT_ID AWS account ID (optional, will be retrieved automatically if not provided)
#   --store-secret             Store credentials in AWS Secrets Manager
#   --skip-policies            Skip creating policies (use existing ones)
#
# Prerequisites:
#   - AWS CLI installed and configured with appropriate credentials
#   - jq installed for JSON processing
#   - Appropriate permissions to create IAM resources

# Exit on error
set -e

# Default values
AWS_REGION="eu-west-2"
USER_NAME="cli-access-user"
ROLE_NAME="Bedrock-Dev-FullAccess-Role"
SECRET_NAME="bedrock-api-config"
KEY_FILE="cli-access-user-keys.json"
STORE_SECRET=false
SKIP_POLICIES=false

# Function to handle errors
handle_error() {
  echo "❌ Error: $1"
  exit 1
}

# Function to check if a command exists
check_command() {
  if ! command -v $1 &> /dev/null; then
    handle_error "$1 is required but not installed. Please install it first."
  fi
}

# Function to display help
display_help() {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -h, --help                 Display this help message"
  echo "  -r, --region REGION        AWS region (default: eu-west-2)"
  echo "  -u, --user USERNAME        IAM user name (default: cli-access-user)"
  echo "  -p, --role ROLE_NAME       IAM role name (default: Bedrock-Dev-FullAccess-Role)"
  echo "  -s, --secret SECRET_NAME   Secret name for storing credentials (default: bedrock-api-config)"
  echo "  -k, --key-file KEY_FILE    File to store access keys (default: cli-access-user-keys.json)"
  echo "  -a, --account-id ACCOUNT_ID AWS account ID (optional, will be retrieved automatically if not provided)"
  echo "  --store-secret             Store credentials in AWS Secrets Manager"
  echo "  --skip-policies            Skip creating policies (use existing ones)"
  exit 0
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      display_help
      ;;
    -r|--region)
      AWS_REGION="$2"
      shift 2
      ;;
    -u|--user)
      USER_NAME="$2"
      shift 2
      ;;
    -p|--role)
      ROLE_NAME="$2"
      shift 2
      ;;
    -s|--secret)
      SECRET_NAME="$2"
      shift 2
      ;;
    -k|--key-file)
      KEY_FILE="$2"
      shift 2
      ;;
    -a|--account-id)
      AWS_ACCOUNT_ID="$2"
      shift 2
      ;;
    --store-secret)
      STORE_SECRET=true
      shift
      ;;
    --skip-policies)
      SKIP_POLICIES=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      display_help
      ;;
  esac
done

# Check for required commands
check_command aws
check_command jq

# Get the AWS account ID dynamically if not provided
if [ -z "$AWS_ACCOUNT_ID" ]; then
  echo "AWS_ACCOUNT_ID not set. Attempting to retrieve it automatically..."
  AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
  if [ $? -ne 0 ]; then
    handle_error "Failed to retrieve AWS account ID automatically. Please set the AWS_ACCOUNT_ID environment variable manually."
  fi
  echo "✅ Retrieved AWS account ID: $AWS_ACCOUNT_ID"
fi

# Function to create IAM user
create_iam_user() {
  echo "Creating IAM user $USER_NAME..."
  if ! aws iam create-user --user-name $USER_NAME 2>/dev/null; then
    echo "⚠️ User $USER_NAME already exists. Continuing..."
  fi

  # Create a policy for the user with minimal permissions
  echo "Creating user policy..."
  cat <<EOF > user-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sts:AssumeRole",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
EOF

  if ! aws iam create-policy \
    --policy-name CLIUserPolicy \
    --policy-document file://user-policy.json 2>/dev/null; then
    echo "⚠️ Policy CLIUserPolicy already exists. Continuing..."
  fi

  # Attach the policy to the user
  if ! aws iam attach-user-policy \
    --user-name $USER_NAME \
    --policy-arn arn:aws:iam::$AWS_ACCOUNT_ID:policy/CLIUserPolicy; then
    handle_error "Failed to attach CLIUserPolicy to user $USER_NAME."
  fi

  # Create access keys for the user
  if [ ! -f "$KEY_FILE" ]; then
    if ! aws iam create-access-key --user-name $USER_NAME > $KEY_FILE; then
      handle_error "Failed to create access keys for user $USER_NAME."
    fi
    echo "Saved access keys to $KEY_FILE"
  else
    echo "⚠️ Access keys file already exists. Skipping key creation."
  fi
}

# Function to create Bedrock policy
create_bedrock_policy() {
  echo "Creating custom policy for BedrockAccessPolicy..."
  cat <<EOF > bedrock-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:ListFoundationModels",
        "bedrock:ListCustomModels"
      ],
      "Resource": "*"
    }
  ]
}
EOF

  if ! aws iam create-policy \
    --policy-name BedrockAccessPolicy \
    --policy-document file://bedrock-policy.json 2>/dev/null; then
    echo "⚠️ Policy BedrockAccessPolicy already exists. Continuing..."
  fi
}

# Function to create role
create_role() {
  echo "Creating role $ROLE_NAME..."
  cat <<EOF > trust-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "AWS": "arn:aws:iam::$AWS_ACCOUNT_ID:root" },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

  if ! aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document file://trust-policy.json 2>/dev/null; then
    echo "⚠️ Role $ROLE_NAME already exists. Continuing..."
  fi
}

# Function to attach policies to role
attach_policies() {
  echo "Attaching policies to role..."

  # Attach Bedrock policy
  BEDROCK_POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='BedrockAccessPolicy'].Arn" --output text)
  if [ -z "$BEDROCK_POLICY_ARN" ]; then
    handle_error "BedrockAccessPolicy not found. Please run create-policies.sh first."
  fi

  if ! aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn $BEDROCK_POLICY_ARN 2>/dev/null; then
    echo "⚠️ BedrockAccessPolicy already attached to role. Continuing..."
  fi

  # Attach other required policies
  POLICY_NAMES=(
    "ECRAccessPolicy"
    "ECSAccessPolicy"
    "EC2AccessPolicy"
    "CloudWatchAccessPolicy"
    "CloudFormationAccessPolicy"
    "S3AccessPolicy"
    "LambdaAccessPolicy"
  )

  for POLICY_NAME in "${POLICY_NAMES[@]}"; do
    POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text)
    if [ -n "$POLICY_ARN" ]; then
      echo "Attaching $POLICY_NAME to role..."
      if ! aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn $POLICY_ARN 2>/dev/null; then
        echo "⚠️ $POLICY_NAME already attached to role. Continuing..."
      fi
    else
      echo "⚠️ Warning: Policy $POLICY_NAME not found. Please run create-policies.sh first."
    fi
  done
}

# Function to assume role
assume_role() {
  echo "Assuming role..."
  SESSION_OUTPUT=$(aws sts assume-role \
    --role-arn arn:aws:iam::$AWS_ACCOUNT_ID:role/$ROLE_NAME \
    --role-session-name CLI-Session)

  if [ $? -ne 0 ]; then
    handle_error "Failed to assume role $ROLE_NAME."
  fi

  export AWS_ACCESS_KEY_ID=$(echo $SESSION_OUTPUT | jq -r '.Credentials.AccessKeyId')
  export AWS_SECRET_ACCESS_KEY=$(echo $SESSION_OUTPUT | jq -r '.Credentials.SecretAccessKey')
  export AWS_SESSION_TOKEN=$(echo $SESSION_OUTPUT | jq -r '.Credentials.SessionToken')

  echo "Temporary credentials exported."
}

# Function to test Bedrock access
test_bedrock() {
  echo "Testing Bedrock access..."
  if ! aws bedrock list-foundation-models --region $AWS_REGION; then
    handle_error "Failed to list Bedrock foundation models. Please check your permissions."
  fi
}

# Function to store credentials in Secrets Manager
store_credentials() {
  echo "Storing credentials in AWS Secrets Manager..."
  
  # Check if access key file exists
  if [ ! -f "$KEY_FILE" ]; then
    handle_error "'$KEY_FILE' not found. Run setup-bedrock.sh first."
  fi

  # Extract credentials using jq
  echo "Extracting credentials from $KEY_FILE..."
  AWS_ACCESS_KEY_ID=$(jq -r '.AccessKey.AccessKeyId' "$KEY_FILE")
  AWS_SECRET_ACCESS_KEY=$(jq -r '.AccessKey.SecretAccessKey' "$KEY_FILE")

  if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    handle_error "Failed to extract credentials from $KEY_FILE. The file may be corrupted."
  fi

  # Build the JSON secret value
  echo "Building secret value..."
  SECRET_VALUE=$(jq -n \
    --arg key "$AWS_ACCESS_KEY_ID" \
    --arg secret "$AWS_SECRET_ACCESS_KEY" \
    '{AWS_ACCESS_KEY_ID: $key, AWS_SECRET_ACCESS_KEY: $secret}')

  # Check if the secret already exists
  echo "Checking if secret '$SECRET_NAME' already exists..."
  EXISTING_SECRET=$(aws secretsmanager list-secrets \
    --region "$AWS_REGION" \
    --query "SecretList[?Name=='$SECRET_NAME']" \
    --output json)

  # Create or update the secret
  if [[ $EXISTING_SECRET == *"$SECRET_NAME"* ]]; then
    echo "🔁 Secret already exists. Updating value..."
    if ! aws secretsmanager update-secret \
      --secret-id "$SECRET_NAME" \
      --secret-string "$SECRET_VALUE" \
      --region "$AWS_REGION"; then
      handle_error "Failed to update secret '$SECRET_NAME'."
    fi
  else
    echo "🆕 Creating new secret '$SECRET_NAME'..."
    if ! aws secretsmanager create-secret \
      --name "$SECRET_NAME" \
      --description "Credentials for Bedrock CLI access" \
      --secret-string "$SECRET_VALUE" \
      --region "$AWS_REGION"; then
      handle_error "Failed to create secret '$SECRET_NAME'."
    fi
  fi

  echo "✅ Secret stored in AWS Secrets Manager: $SECRET_NAME"
}

# Main execution
echo "Starting AWS Bedrock setup..."

# Create IAM user
create_iam_user

# Create Bedrock policy if not skipping
if [ "$SKIP_POLICIES" = false ]; then
  create_bedrock_policy
fi

# Create role
create_role

# Attach policies
attach_policies

# Assume role
assume_role

# Test Bedrock access
test_bedrock

# Store credentials in Secrets Manager if requested
if [ "$STORE_SECRET" = true ]; then
  store_credentials
fi

echo "✅ AWS Bedrock setup completed successfully!" 