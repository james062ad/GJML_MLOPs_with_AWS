#!/bin/bash

# setup-aws-bedrock.sh
# Full AWS Bedrock setup script (Final Version with .env backup)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# --- GLOBAL SETTINGS ---
AWS_REGION="eu-west-2"
USER_NAME="cli-access-user"
ROLE_NAME="Bedrock-Dev-FullAccess-Role"
SECRET_NAME="bedrock-api-config"
KEY_FILE="cli-access-user-keys.json"
STORE_SECRET=true
SKIP_POLICIES=false

TARGET_APP_FOLDER="rag-app-aws"        # <<< Adjustable app folder
TARGET_ENV_FILE="$TARGET_APP_FOLDER/.env"

# --- FUNCTIONS ---

handle_error() {
  echo -e "${RED}❌ Error:${NC} $1"
  exit 1
}

check_command() {
  if ! command -v $1 &> /dev/null; then
    handle_error "$1 is required but not installed. Please install it first."
  fi
}

verify_or_prompt_credentials() {
  echo -e "${BLUE}🔍 Checking AWS CLI authentication...${NC}"
  if ! aws sts get-caller-identity --output text &> /dev/null; then
    echo -e "${YELLOW}❗ No valid AWS credentials found.${NC}"
    read -p "Enter AWS Access Key ID: " ACCESS_KEY_ID
    read -s -p "Enter AWS Secret Access Key: " SECRET_ACCESS_KEY
    echo
    read -p "Enter AWS Default Region (default: eu-west-2): " REGION_INPUT
    AWS_REGION=${REGION_INPUT:-eu-west-2}

    aws configure set aws_access_key_id "$ACCESS_KEY_ID"
    aws configure set aws_secret_access_key "$SECRET_ACCESS_KEY"
    aws configure set region "$AWS_REGION"
    aws configure set output json

    echo -e "${GREEN}✅ AWS CLI configured.${NC}"
  else
    echo -e "${GREEN}✅ AWS CLI is authenticated.${NC}"
  fi
}

create_iam_user() {
  echo -e "${BLUE}👤 Creating IAM user: $USER_NAME...${NC}"
  if ! aws iam create-user --user-name $USER_NAME 2>/dev/null; then
    echo -e "${YELLOW}⚠️ User already exists. Skipping.${NC}"
  fi
  if [ ! -f "$KEY_FILE" ]; then
    aws iam create-access-key --user-name $USER_NAME > "$KEY_FILE"
    echo -e "${GREEN}✅ Access keys saved to $KEY_FILE.${NC}"
  else
    echo -e "${YELLOW}⚠️ Access keys file already exists. Skipping.${NC}"
  fi
}

create_bedrock_policy() {
  echo -e "${BLUE}📜 Creating Bedrock policy...${NC}"
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
    echo -e "${YELLOW}⚠️ Policy already exists. Continuing.${NC}"
  fi
}

wait_for_policy() {
  echo -e "${BLUE}⏳ Waiting for BedrockAccessPolicy...${NC}"
  for i in {1..10}; do
    if aws iam get-policy --policy-arn "$1" > /dev/null 2>&1; then
      echo -e "${GREEN}✅ BedrockAccessPolicy available.${NC}"
      return
    fi
    echo "Waiting... ($i)"
    sleep 5
  done
  handle_error "BedrockAccessPolicy did not propagate."
}

create_role() {
  echo -e "${BLUE}🎭 Creating role: $ROLE_NAME...${NC}"
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
    echo -e "${YELLOW}⚠️ Role already exists. Continuing.${NC}"
  fi
}

attach_policies() {
  echo -e "${BLUE}📎 Attaching policies...${NC}"
  BEDROCK_POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='BedrockAccessPolicy'].Arn" --output text)
  aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AdministratorAccess || true
  sleep 2
  aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn $BEDROCK_POLICY_ARN || true
  sleep 2
}

assume_role() {
  echo -e "${BLUE}🔄 Assuming role...${NC}"
  AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
  sleep 10
  SESSION_OUTPUT=$(aws sts assume-role \
    --role-arn arn:aws:iam::$AWS_ACCOUNT_ID:role/$ROLE_NAME \
    --role-session-name CLI-Session)
  export AWS_ACCESS_KEY_ID=$(echo "$SESSION_OUTPUT" | jq -r '.Credentials.AccessKeyId')
  export AWS_SECRET_ACCESS_KEY=$(echo "$SESSION_OUTPUT" | jq -r '.Credentials.SecretAccessKey')
  export AWS_SESSION_TOKEN=$(echo "$SESSION_OUTPUT" | jq -r '.Credentials.SessionToken')
  echo -e "${GREEN}✅ Role assumed successfully.${NC}"
}

setup_env_file() {
  echo -e "${BLUE}📝 Updating $TARGET_ENV_FILE safely...${NC}"

  mkdir -p "$TARGET_APP_FOLDER"
  touch "$TARGET_ENV_FILE"

  # Backup existing .env first
  if [ -f "$TARGET_ENV_FILE" ]; then
    cp "$TARGET_ENV_FILE" "$TARGET_ENV_FILE.bak"
    echo -e "${YELLOW}⚠️ Backup created at $TARGET_ENV_FILE.bak${NC}"
  fi

  # Remove old AWS keys
  sed -i '' '/^AWS_ACCESS_KEY_ID=/d' "$TARGET_ENV_FILE"
  sed -i '' '/^AWS_SECRET_ACCESS_KEY=/d' "$TARGET_ENV_FILE"
  sed -i '' '/^AWS_SESSION_TOKEN=/d' "$TARGET_ENV_FILE"
  sed -i '' '/^AWS_REGION=/d' "$TARGET_ENV_FILE"
  sed -i '' '/^BEDROCK_MODEL_ID=/d' "$TARGET_ENV_FILE"
  sed -i '' '/^BEDROCK_EMBEDDING_MODEL_ID=/d' "$TARGET_ENV_FILE"

  # Append new credentials
  {
    echo "AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}"
    echo "AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}"
    echo "AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}"
    echo "AWS_REGION=${AWS_REGION}"
  } >> "$TARGET_ENV_FILE"

  chmod 600 "$TARGET_ENV_FILE"

  echo -e "${GREEN}✅ AWS credentials safely updated in $TARGET_ENV_FILE.${NC}"
}

choose_bedrock_models() {
  echo -e "${BLUE}🔎 Selecting Bedrock models...${NC}"
  MODELS_JSON=$(aws bedrock list-foundation-models --region "$AWS_REGION")
  MODEL_IDS=($(echo "$MODELS_JSON" | jq -r '.modelSummaries[].modelId'))
  MODEL_NAMES=($(echo "$MODELS_JSON" | jq -r '.modelSummaries[].modelName'))

  if [ ${#MODEL_IDS[@]} -eq 0 ]; then
    handle_error "No Bedrock models found."
  fi

  echo
  echo "Available generation/chat models:"
  for i in "${!MODEL_IDS[@]}"; do
    printf "%3d) %s (%s)\n" $((i+1)) "${MODEL_NAMES[$i]}" "${MODEL_IDS[$i]}"
  done
  echo
  read -p "Select a generation/chat model (number): " MODEL_SELECTION
  BEDROCK_MODEL_ID=${MODEL_IDS[$((MODEL_SELECTION-1))]}

  echo
  echo "Available embedding models:"
  for i in "${!MODEL_IDS[@]}"; do
    printf "%3d) %s (%s)\n" $((i+1)) "${MODEL_NAMES[$i]}" "${MODEL_IDS[$i]}"
  done
  echo
  read -p "Select an embedding model (number): " EMBEDDING_SELECTION
  BEDROCK_EMBEDDING_MODEL_ID=${MODEL_IDS[$((EMBEDDING_SELECTION-1))]}

  echo "BEDROCK_MODEL_ID=${BEDROCK_MODEL_ID}" >> "$TARGET_ENV_FILE"
  echo "BEDROCK_EMBEDDING_MODEL_ID=${BEDROCK_EMBEDDING_MODEL_ID}" >> "$TARGET_ENV_FILE"

  echo -e "${GREEN}✅ Models saved to $TARGET_ENV_FILE.${NC}"
}

# --- SCRIPT START ---

echo -e "${BLUE}🚀 Starting AWS Bedrock Setup Script...${NC}"

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
setup_env_file
choose_bedrock_models

echo -e "${GREEN}✅ AWS Bedrock setup completed successfully!${NC}"