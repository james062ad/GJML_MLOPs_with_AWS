# AWS Setup Guide for Bedrock Access

This guide provides step-by-step instructions for setting up AWS Bedrock access for the MLOps project. It covers everything from initial AWS account setup to configuring the necessary IAM resources and testing your access.

> **Note**: This guide complements the AWS section in the main [README.md](../README.md). For a high-level overview, refer to that document first.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS Account Setup](#aws-account-setup)
3. [AWS CLI Configuration](#aws-cli-configuration)
4. [Setting Up Bedrock Access](#setting-up-bedrock-access)
5. [Using the Setup Script](#using-the-setup-script)
6. [Adapting RAG App to Work with AWS Bedrock](#adapting-rag-app-to-work-with-aws-bedrock)

## Prerequisites

Before you begin, ensure you have:

- An AWS account (or the ability to create one)
- AWS CLI installed on your machine
- `jq` command-line tool installed
- Basic understanding of AWS IAM concepts

### Installing Prerequisites

#### AWS CLI Installation

**macOS:**
```bash
brew install awscli
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Windows:**
Download and run the [AWS CLI MSI installer](https://awscli.amazonaws.com/AWSCLIV2.msi).

#### jq Installation

**macOS:**
```bash
brew install jq
```

**Linux:**
```bash
sudo apt-get install jq
```

**Windows:**
Download from [jq's official website](https://stedolan.github.io/jq/download/) or use Chocolatey:
```bash
choco install jq
```

## AWS Account Setup

1. **Create an AWS Account:**
   - Go to [AWS Sign Up](https://portal.aws.amazon.com/billing/signup)
   - Follow the registration process
   - You'll need a credit card for verification (AWS has a free tier for many services)

2. **Create an IAM User:**
   - Log into the AWS Management Console (https://console.aws.com)
   - Search for "IAM" in the top search bar
   - Click on "IAM" in the search results
   - In the left navigation pane, click on "Users"
   - Click the "Create user" button
   - Enter a name for your user (e.g., "cli-access-user")
   - Click "Next"
   - For permissions, select "Attach policies directly"
   - Search for and select "AdministratorAccess" (for initial setup - you can restrict this later)
   - Click "Next"
   - Review the details and click "Create user"
   - After creation, click on the user's name
   - Go to the "Security credentials" tab
   - Under "Access keys", click "Create access key"
   - Choose "Command Line Interface (CLI)"
   - Acknowledge the recommendations and click "Next"
   - Click "Create access key"
   - **IMPORTANT**: Save both the Access Key ID and Secret Access Key - you won't see the secret key again!

3. **Set Up Budget Alerts:**
   - Go to the AWS Billing Dashboard
   - Select "Budgets" from the left navigation
   - Click "Create budget"
   - Set a monthly budget (e.g., $30) with alerts at 80% and 100%
   - This helps prevent unexpected charges

   ![Setting up Budget Alerts](../assets/image-bedrock-budget-alert.png)

4. **Enable Bedrock Service:**
   - Go to the AWS Bedrock console
   - Click "Get Started" or "Enable Bedrock"
   - Enable the models you plan to use (at minimum, enable Titan Text models)

## AWS CLI Configuration

1. **Configure AWS CLI with your credentials:**
   ```bash
   aws configure
   ```
   - Enter your AWS Access Key ID
   - Enter your AWS Secret Access Key
   - Enter your default region (e.g., `eu-west-2`)
   - Enter your preferred output format (e.g., `json`)

   ![AWS CLI Configuration](../assets/image-aws-cli-configure.png)

2. **Verify your configuration:**
   ```bash
   aws sts get-caller-identity
   ```
   You should see output similar to:
   ```json
   {
     "UserId": "AIDAEXAMPLEEXAMPLEEXAMPLE",
     "Account": "123456789012",
     "Arn": "arn:aws:iam::123456789012:user/YourUsername"
   }
   ```

## Setting Up Bedrock Access

The improved setup process is now fully automated using the `setup-aws-bedrock.sh` script. This script handles all the necessary steps to set up AWS Bedrock access, including:

1. Creating an IAM user with appropriate permissions
2. Creating a custom Bedrock access policy
3. Creating an IAM role with the necessary permissions
4. Attaching policies to the role
5. Assuming the role to get temporary credentials
6. Testing Bedrock access
7. Optionally storing credentials in AWS Secrets Manager

## Using the Setup Script

The `setup-aws-bedrock.sh` script is designed to be a zero-touch solution for setting up AWS Bedrock access. It handles all the necessary steps automatically, with configurable options.

### Basic Usage

```bash
# Make the script executable
chmod +x setup-aws-bedrock.sh

# Run the script with default settings
./setup-aws-bedrock.sh
```

### Script Options

The script accepts several command-line options to customize its behavior:

```bash
./setup-aws-bedrock.sh [options]
```

Available options:
- `--region REGION`: Set the AWS region (default: eu-west-2)
- `--user USER_NAME`: Set the IAM user name (default: cli-access-user)
- `--role ROLE_NAME`: Set the IAM role name (default: Bedrock-Dev-FullAccess-Role)
- `--secret SECRET_NAME`: Set the Secrets Manager secret name (default: bedrock-api-config)
- `--key-file KEY_FILE`: Set the access key file name (default: cli-access-user-keys.json)
- `--store-secret`: Store credentials in Secrets Manager (default: true)
- `--skip-policies`: Skip policy creation (default: false)
- `--enable-models`: Enable Bedrock models (default: false)
- `--budget BUDGET_AMOUNT`: Set budget amount (default: 30)
- `--help`: Display help information

### What the Script Does

The script performs the following operations:

1. **Verifies AWS CLI Authentication**:
   ```bash
   # Checks if AWS CLI is authenticated
   aws sts get-caller-identity --output text
   
   # If not authenticated, prompts for credentials
   read -p "Enter AWS Access Key ID: " ACCESS_KEY_ID
   read -s -p "Enter AWS Secret Access Key: " SECRET_ACCESS_KEY
   echo
   read -p "Enter your AWS Default Region (default: eu-west-2): " REGION_INPUT
   ```

2. **Creates an IAM User**:
   ```bash
   # Creates an IAM user with the specified name
   aws iam create-user --user-name $USER_NAME
   
   # Creates access keys for the user and saves them to a file
   aws iam create-access-key --user-name $USER_NAME > "$KEY_FILE"
   ```

3. **Creates a Custom Bedrock Access Policy**:
   ```bash
   # Creates a JSON policy document
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
   
   # Creates the policy in AWS
   aws iam create-policy --policy-name BedrockAccessPolicy --policy-document file://bedrock-policy.json
   ```

4. **Creates an IAM Role**:
   ```bash
   # Gets the AWS account ID
   AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
   
   # Creates a trust policy document
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
   
   # Creates the role in AWS
   aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document file://trust-policy.json
   ```

5. **Attaches Policies to the Role**:
   ```bash
   # Gets the Bedrock policy ARN
   BEDROCK_POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='BedrockAccessPolicy'].Arn" --output text)
   
   # Attaches the AdministratorAccess policy
   aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
   
   # Attaches the Bedrock access policy
   aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn $BEDROCK_POLICY_ARN
   ```

6. **Assumes the Role to Get Temporary Credentials**:
   ```bash
   # Waits for IAM permissions to propagate
   sleep 10
   
   # Assumes the role and gets temporary credentials
   SESSION_OUTPUT=$(aws sts assume-role \
     --role-arn arn:aws:iam::$AWS_ACCOUNT_ID:role/$ROLE_NAME \
     --role-session-name CLI-Session)
   
   # Exports the temporary credentials as environment variables
   export AWS_ACCESS_KEY_ID=$(echo "$SESSION_OUTPUT" | jq -r '.Credentials.AccessKeyId')
   export AWS_SECRET_ACCESS_KEY=$(echo "$SESSION_OUTPUT" | jq -r '.Credentials.SecretAccessKey')
   export AWS_SESSION_TOKEN=$(echo "$SESSION_OUTPUT" | jq -r '.Credentials.SessionToken')
   ```

7. **Tests Bedrock Access**:
   ```bash
   # Lists available Bedrock foundation models
   aws bedrock list-foundation-models --region $AWS_REGION
   ```

8. **Stores Credentials in Secrets Manager** (if enabled):
   ```bash
   # Gets the access keys from the key file
   CLI_ACCESS_KEY=$(jq -r '.AccessKey.AccessKeyId' "$KEY_FILE")
   CLI_SECRET_KEY=$(jq -r '.AccessKey.SecretAccessKey' "$KEY_FILE")
   
   # Creates a JSON secret value
   SECRET_VALUE=$(jq -n \
     --arg key "$CLI_ACCESS_KEY" \
     --arg secret "$CLI_SECRET_KEY" \
     '{AWS_ACCESS_KEY_ID: $key, AWS_SECRET_ACCESS_KEY: $secret}')
   
   # Creates or updates the secret in Secrets Manager
   aws secretsmanager create-secret \
     --name "$SECRET_NAME" \
     --description "CLI access credentials for Bedrock" \
     --secret-string "$SECRET_VALUE" \
     --region "$AWS_REGION"
   ```

### Example Usage Scenarios

1. **Basic Setup with Default Settings**:
   ```bash
   ./setup-aws-bedrock.sh
   ```

2. **Custom Region and User**:
   ```bash
   ./setup-aws-bedrock.sh --region us-east-1 --user my-user
   ```

3. **Skip Storing Credentials in Secrets Manager**:
   ```bash
   ./setup-aws-bedrock.sh --store-secret false
   ```

4. **Skip Policy Creation (Use Existing Policies)**:
   ```bash
   ./setup-aws-bedrock.sh --skip-policies
   ```

5. **Set Up Budget Alerts with a Custom Amount**:
   ```bash
   ./setup-aws-bedrock.sh --budget 50
   ```

6. **Enable Bedrock Models**:
   ```bash
   ./setup-aws-bedrock.sh --enable-models
   ```

7. **Display Help Information**:
   ```bash
   ./setup-aws-bedrock.sh --help
   ```

## Adapting RAG App to Work with AWS Bedrock

To transition the RAG application from using direct AWS services to AWS Bedrock, several files need to be modified. This section outlines the necessary changes and what they replace.

### Files Requiring Changes

#### 1. Configuration Files

**`rag-app-aws/server/src/config.py`**
- **Add:** AWS Bedrock configuration parameters
  ```python
  # AWS Bedrock config
  aws_region: str = Field(..., env="AWS_REGION")
  aws_access_key_id: str = Field(..., env="AWS_ACCESS_KEY_ID")
  aws_secret_access_key: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
  aws_session_token: str = Field(None, env="AWS_SESSION_TOKEN")  # Optional, for temporary credentials
  bedrock_model_id: str = Field(..., env="BEDROCK_MODEL_ID")  # e.g., "amazon.titan-text-express-v1"
  ```
- **Replace:** Any existing AWS service-specific configuration parameters

**`rag-app-aws/server/src/config_loader.py`**
- **Add:** Bedrock configuration loading logic
  ```python
  # Handle Bedrock configuration
  if cls._config.get("generation", {}).get("model") == "bedrock":
      gen_config = cls._config.get("generation", {})
      
      # Update Bedrock settings
      if hasattr(settings, "bedrock_model_id"):
          settings.bedrock_model_id = gen_config.get("bedrock_model_id")
      if hasattr(settings, "aws_region"):
          settings.aws_region = gen_config.get("aws_region")
  ```
- **Add:** Bedrock-specific configuration retrieval methods
  ```python
  @classmethod
  def is_using_bedrock(cls) -> bool:
      """Check if AWS Bedrock is enabled in config."""
      return cls._config.get("generation", {}).get("model") == "bedrock"
  ```
- **Replace:** Any existing AWS service-specific configuration loading logic

#### 2. Service Implementation Files

**`rag-app-aws/server/src/services/generation_service.py`**
- **Add:** Bedrock client initialization
  ```python
  # Initialize AWS Bedrock client
  bedrock_client = boto3.client(
      service_name='bedrock-runtime',
      region_name=settings.aws_region,
      aws_access_key_id=settings.aws_access_key_id,
      aws_secret_access_key=settings.aws_secret_access_key,
      aws_session_token=settings.aws_session_token
  )
  ```
- **Add:** Bedrock API invocation code
  ```python
  # Prepare the request body for Bedrock
  request_body = {
      "prompt": prompt,
      "maxTokens": max_tokens,
      "temperature": temperature,
      "topP": top_p,
      "stopSequences": stop_sequences
  }
  
  # Call Bedrock API
  response = bedrock_client.invoke_model(
      modelId=settings.bedrock_model_id,
      body=json.dumps(request_body)
  )
  
  # Parse the response
  response_body = json.loads(response.get('body').read())
  generated_text = response_body.get('completion', '')
  ```
- **Replace:** Any existing AWS service-specific generation code (e.g., SageMaker, Lambda)

#### 3. Embedding Service

**`rag-app-aws/server/src/ingestion/embeddings.py`**
- **Add:** Bedrock embedding model initialization
  ```python
  # Initialize Bedrock client for embeddings
  bedrock_client = boto3.client(
      service_name='bedrock-runtime',
      region_name=settings.aws_region,
      aws_access_key_id=settings.aws_access_key_id,
      aws_secret_access_key=settings.aws_secret_access_key,
      aws_session_token=settings.aws_session_token
  )
  ```
- **Add:** Bedrock embedding generation code
  ```python
  def get_embeddings(texts):
      embeddings = []
      for text in texts:
          request_body = {
              "inputText": text
          }
          
          response = bedrock_client.invoke_model(
              modelId=settings.bedrock_embedding_model_id,
              body=json.dumps(request_body)
          )
          
          response_body = json.loads(response.get('body').read())
          embedding = response_body.get('embedding', [])
          embeddings.append(embedding)
      
      return embeddings
  ```
- **Replace:** The current SentenceTransformer implementation (`model = SentenceTransformer('all-MiniLM-L6-v2')`)

#### 4. Dependencies

**`rag-app-aws/pyproject.toml`**
- **Add:** AWS Bedrock SDK dependency
  ```toml
  [tool.poetry.dependencies]
  boto3 = "^1.28.0"
  ```
- **Replace:** Any AWS service-specific SDK dependencies that are no longer needed

### Implementation Strategy

1. **Configuration First:** Start by updating the configuration files to support Bedrock parameters.
2. **Service Implementation:** Modify the generation service to use Bedrock instead of direct AWS services.
3. **Embedding Service:** Update the embedding service to use Bedrock's embedding models.
4. **Testing:** Test each component individually before integrating them.
5. **Fallback Mechanism:** Implement a fallback mechanism to use the original AWS services if Bedrock is not available.

### Environment Variables

Ensure the following environment variables are set:
- `AWS_REGION`: The AWS region where Bedrock is available
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `AWS_SESSION_TOKEN`: (Optional) Your AWS session token for temporary credentials
- `BEDROCK_MODEL_ID`: The ID of the Bedrock model to use (e.g., "amazon.titan-text-express-v1")
- `BEDROCK_EMBEDDING_MODEL_ID`: The ID of the Bedrock embedding model to use

### Testing Bedrock Integration

After implementing the changes, test the Bedrock integration with:

```bash
# Test Bedrock model access
aws bedrock list-foundation-models --region $AWS_REGION

# Test Bedrock model invocation
aws bedrock invoke-model \
  --model-id amazon.titan-text-express-v1 \
  --body '{"prompt": "Hello, how are you?", "maxTokens": 100}' \
  --region $AWS_REGION
```