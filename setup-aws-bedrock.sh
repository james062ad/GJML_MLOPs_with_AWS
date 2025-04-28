#!/bin/bash

# setup-aws-bedrock.sh
# Full zero-touch AWS Bedrock setup script (Final version)

# Exit on error
set -e

# Default values
AWS_REGION="eu-west-2"
USER_NAME="cli-access-user"
ROLE_NAME="Bedrock-Dev-FullAccess-Role"
SECRET_NAME="bedrock-api-config"
KEY_FILE="cli-access-user-keys.json"
STORE_SECRET=true
SKIP_POLICIES=false
ENABLE_MODELS=false
BUDGET_AMOUNT=30

# --- FUNCTIONS ---

handle_error() {
  echo "❌ Error: $1"
  exit 1
}

check_command() {
  if ! command -v $1 &> /dev/null; then
    handle_error "$1 is required but not installed. Please install it first."
  fi
}

verify_or_prompt_credentials() {
  echo "🔍 Checking AWS CLI authentication..."
  if ! aws sts get-caller-identity --output text &> /dev/null; then
    echo "❗ No valid AWS credentials found."

    read -p "Enter AWS Access Key ID: " ACCESS_KEY_ID
    read -s -p "Enter AWS Secret Access Key: " SECRET_ACCESS_KEY
    echo
    read -p "Enter your AWS Default Region (default: eu-west-2): " REGION_INPUT
    AWS_REGION=${REGION_INPUT:-eu-west-2}

    aws configure set aws_access_key_id "$ACCESS_KEY_ID"
    aws configure set aws_secret_access_key "$SECRET_ACCESS_KEY"
    aws configure set region "$AWS_REGION"
    aws configure set output json

    echo "✅ AWS CLI configured."

    if ! aws sts get-caller-identity --output text &> /dev/null; then
      handle_error "Authentication failed even after providing credentials."
    fi
  else
    echo "✅ AWS CLI is authenticated."
  fi
}

create_iam_user() {
  echo "👤 Creating IAM user: $USER_NAME..."
  if ! aws iam create-user --user-name $USER_NAME 2>/dev/null; then
    echo "⚠️ User already exists. Skipping user creation."
  fi

  if [ ! -f "$KEY_FILE" ]; then
    aws iam create-access-key --user-name $USER_NAME > "$KEY_FILE"
    echo "✅ Access keys saved to $KEY_FILE"
  else
    echo "⚠️ Access keys file already exists. Skipping access key creation."
  fi
}

create_bedrock_policy() {
  echo "📜 Creating custom BedrockAccessPolicy..."
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

  if ! aws iam create-policy --policy-name BedrockAccessPolicy --policy-document file://bedrock-policy.json 2>/dev/null; then
    echo "⚠️ Policy already exists. Continuing."
  fi
}

wait_for_policy() {
  echo "⏳ Waiting for BedrockAccessPolicy to be available..."
  for i in {1..10}; do
    if aws iam get-policy --policy-arn "$1" > /dev/null 2>&1; then
      echo "✅ BedrockAccessPolicy is now available."
      return 0
    fi
    echo "⏳ Still waiting for BedrockAccessPolicy (retry $i)..."
    sleep 5
  done
  handle_error "BedrockAccessPolicy was not available after waiting."
}

create_role() {
  echo "🎭 Creating role: $ROLE_NAME..."
  AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

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

  if ! aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document file://trust-policy.json 2>/dev/null; then
    echo "⚠️ Role already exists. Continuing."
  fi
}

attach_policies() {
  echo "📎 Attaching policies to role..."
  
  BEDROCK_POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='BedrockAccessPolicy'].Arn" --output text)

  aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AdministratorAccess || true
  sleep 2
  aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn $BEDROCK_POLICY_ARN || true
  sleep 2
  
  echo "✅ Policies attached to role."
}

assume_role() {
  echo "🔄 Assuming role..."
  AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

  echo "⏳ Waiting 10 seconds for IAM permissions to propagate..."
  sleep 10

  SESSION_OUTPUT=$(aws sts assume-role \
    --role-arn arn:aws:iam::$AWS_ACCOUNT_ID:role/$ROLE_NAME \
    --role-session-name CLI-Session)

  export AWS_ACCESS_KEY_ID=$(echo "$SESSION_OUTPUT" | jq -r '.Credentials.AccessKeyId')
  export AWS_SECRET_ACCESS_KEY=$(echo "$SESSION_OUTPUT" | jq -r '.Credentials.SecretAccessKey')
  export AWS_SESSION_TOKEN=$(echo "$SESSION_OUTPUT" | jq -r '.Credentials.SessionToken')

  echo "✅ Temporary credentials exported."
}

test_bedrock() {
  echo "🧪 Testing Bedrock access..."
  if aws bedrock list-foundation-models --region $AWS_REGION; then
    echo "✅ Bedrock access verified!"
  else
    echo "❌ Failed to access Bedrock API. Please check permissions manually."
    exit 1
  fi
}

store_credentials() {
  echo "🔐 Storing CLI credentials into AWS Secrets Manager..."

  CLI_ACCESS_KEY=$(jq -r '.AccessKey.AccessKeyId' "$KEY_FILE")
  CLI_SECRET_KEY=$(jq -r '.AccessKey.SecretAccessKey' "$KEY_FILE")

  SECRET_VALUE=$(jq -n \
    --arg key "$CLI_ACCESS_KEY" \
    --arg secret "$CLI_SECRET_KEY" \
    '{AWS_ACCESS_KEY_ID: $key, AWS_SECRET_ACCESS_KEY: $secret}')

  if aws secretsmanager describe-secret --secret-id "$SECRET_NAME" --region "$AWS_REGION" > /dev/null 2>&1; then
    echo "🔁 Secret already exists. Updating..."
    aws secretsmanager update-secret \
      --secret-id "$SECRET_NAME" \
      --secret-string "$SECRET_VALUE" \
      --region "$AWS_REGION"
  else
    echo "🆕 Creating new secret..."
    aws secretsmanager create-secret \
      --name "$SECRET_NAME" \
      --description "CLI access credentials for Bedrock" \
      --secret-string "$SECRET_VALUE" \
      --region "$AWS_REGION"
  fi

  echo "✅ Secret stored successfully: $SECRET_NAME"
}

# --- SCRIPT START ---

echo "🚀 Starting AWS Bedrock Setup Script..."

check_command aws
check_command jq

verify_or_prompt_credentials

create_iam_user

if [ "$SKIP_POLICIES" = false ]; then
  create_bedrock_policy
fi

BEDROCK_POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='BedrockAccessPolicy'].Arn" --output text)
wait_for_policy "$BEDROCK_POLICY_ARN"

create_role

attach_policies

assume_role

test_bedrock

if [ "$STORE_SECRET" = true ]; then
  store_credentials
fi

echo "✅ AWS Bedrock setup completed successfully!"