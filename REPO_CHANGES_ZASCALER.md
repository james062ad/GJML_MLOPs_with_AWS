# Critical Changes Required for oxford-genai-llmops-project

This document outlines the critical changes needed to make the [oxford-genai-llmops-project](https://github.com/AndyMc629/oxford-genai-llmops-project) repository work properly. These changes address compatibility issues, dependency problems, and configuration errors that prevent the application from running correctly.

## Summary of Changes

The following key changes were implemented to improve the repository:

1. **Certificate Configuration**: Added Zscaler certificate support to Dockerfiles to handle corporate network requirements. [See Section 1](#1-certificate-configuration)

2. **PostgreSQL Configuration**: Updated the PostgreSQL Docker Compose file to include proper initialization scripts and environment checks. [See Section 2](#2-postgresql-configuration)

3. **CI/CD Pipeline**: Implemented a comprehensive CI pipeline using GitHub Actions to automate testing and deployment. [See Section 3](#3-cicd-configuration)

4. **Streamlit App Improvements**: Added improvements to the Streamlit app for better user experience. [See Section 4](#4-streamlit-app-improvements)

## 1. Certificate Configuration

### 1.1 Development Container Dockerfile

**Why**: The development container needs proper certificate configuration to work in corporate environments.

The development container Dockerfile in `.devcontainer/Dockerfile` was updated with the following changes:

```dockerfile
#FROM mcr.microsoft.com/devcontainers/python:1-3.12-bullseye
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# ✅ Trust Zscaler cert early (use .crt extension for update-ca-certificates)
COPY ZscalerRootCertificate-2048-SHA256.pem /usr/local/share/ca-certificates/zscaler.crt
RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates

# ✅ Make pip, curl, and Node respect custom certs
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt

# Install AWS CLI for aarch64, refer to docs for more info https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl unzip && \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip" && \
    unzip -o awscliv2.zip && \
    ./aws/install && \
    rm -rf awscliv2.zip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install git and allow for git push/pull from devcontainer.
RUN apt-get install git && \
    git config --global --add safe.directory /workspaces/oxford-genai-capstone

# Install python dependencies
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Final cleanup
RUN rm -rf /var/lib/apt/lists/*s
```

Key changes from the original file:
1. Added Zscaler certificate configuration at the beginning of the Dockerfile
2. Added environment variables to make pip, curl, and Node respect the custom certificates
3. Updated the base image to use bookworm instead of bullseye
4. Added proper cleanup steps to reduce image size

### 1.2 PostgreSQL Dockerfile

**Why**: Corporate environments often use Zscaler for network security, which requires proper certificate configuration for secure connections.

The PostgreSQL Dockerfile in `rag-app/deploy/docker/postgres/pgvector2.Dockerfile` was updated with the following changes:

```dockerfile
# Stage 1: Certificate setup with HTTP repo workaround
FROM alpine:latest AS cert-setup

# Override repositories to use HTTP instead of HTTPS to skip SSL verification
RUN echo "http://dl-cdn.alpinelinux.org/alpine/v3.21/main" > /etc/apk/repositories && \
    echo "http://dl-cdn.alpinelinux.org/alpine/v3.21/community" >> /etc/apk/repositories && \
    apk update && apk add --no-cache ca-certificates && update-ca-certificates

COPY ZscalerRootCertificate-2048-SHA256.pem /usr/local/share/ca-certificates/zscaler.crt

# Re-run after copy to add Zscaler cert
RUN update-ca-certificates

# Stage 2: Build pgvector with Zscaler cert available
FROM postgres:alpine AS builder

# Copy trusted certs
COPY --from=cert-setup /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt

RUN apk update && apk add --no-cache \
    build-base \
    git \
    postgresql-dev \
    clang \
    llvm-dev

WORKDIR /build

RUN git clone --branch v0.5.0 https://github.com/pgvector/pgvector.git && \
    cd pgvector && make && make install

# Stage 3: Final image with pgvector + Zscaler certs
FROM postgres:alpine

# Copy trusted certs and setup HTTP repositories
COPY --from=cert-setup /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
RUN echo "http://dl-cdn.alpinelinux.org/alpine/v3.21/main" > /etc/apk/repositories && \
    echo "http://dl-cdn.alpinelinux.org/alpine/v3.21/community" >> /etc/apk/repositories

# Install locale packages to fix the locale warning
RUN apk update && apk add --no-cache \
    musl-locales \
    musl-locales-lang \
    tzdata

# Set default locale
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

COPY --from=builder /usr/local/lib/postgresql/ /usr/local/lib/postgresql/
COPY --from=builder /usr/local/share/postgresql/ /usr/local/share/postgresql/

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pg_isready -U ${POSTGRES_USER:-postgres} || exit 1
```

Key changes from the original file:
1. Added a multi-stage build process with a dedicated certificate setup stage
2. Added Zscaler certificate configuration to handle corporate network requirements
3. Configured HTTP repositories to bypass SSL verification issues
4. Added locale configuration to fix locale warnings
5. Added a healthcheck configuration for better container orchestration

## 2. PostgreSQL Configuration

### 2.1 Docker Compose Setup

**Why**: The PostgreSQL service needs proper configuration to ensure it initializes correctly with the pgvector extension.

The Docker Compose file in `rag-app/deploy/docker/postgres/docker-compose.yaml` was updated with the following changes:

```yaml
services:
  postgres:
    build:
      context: .
      dockerfile: pgvector2.Dockerfile
    ports:
      - "${POSTGRES_PORT}:5432"
    volumes:
      - ./data:/var/lib/postgresql/data
      - ./init_pgvector.sql:/docker-entrypoint-initdb.d/init_pgvector.sql
      - ./check_env.sh:/docker-entrypoint-initdb.d/check_env.sh
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    command: >
      bash -c "
        chmod +x /docker-entrypoint-initdb.d/check_env.sh &&
        /docker-entrypoint-initdb.d/check_env.sh &&
        docker-entrypoint.sh postgres
      "
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

Key changes from the original file:
1. Added a `check_env.sh` script to verify environment variables before starting PostgreSQL
2. Added a custom command to execute the environment check script
3. Added a healthcheck configuration to ensure the database is ready before other services connect to it
4. Updated the healthcheck to use the correct database name

### 2.2 Vector Index Creation

**Why**: Efficient vector similarity search requires proper indexing for performance.

The `init_pgvector.sql` file includes the following important line:

```sql
CREATE INDEX IF NOT EXISTS papers_embedding_idx ON papers USING ivfflat (embedding vector_cosine_ops);
```

This line creates an IVF-Flat index on the embedding column, which significantly improves the performance of vector similarity searches. The IVF-Flat index is particularly well-suited for high-dimensional vector data like embeddings, as it:

1. Partitions the vector space into clusters (IVF - Inverted File)
2. Uses a flat structure within each cluster for exact search
3. Optimizes for cosine similarity operations with the `vector_cosine_ops` operator class

Without this index, vector similarity searches would require a full table scan, which becomes increasingly slow as the number of vectors grows. The index reduces query time from O(n) to O(log n) in most cases.

## 3. CI/CD Configuration

### 3.1 GitHub Actions Setup

**Why**: Proper CI/CD configuration ensures reliable automated testing and deployment.

The repository now uses a comprehensive CI pipeline defined in `.github/workflows/ci-initialise.yml`. Here's the actual content of the ci-initialise.yml file:

```yaml
# This workflow runs automated tests whenever code is pushed to any branch
name: CI Pipeline

# Define when the workflow should run
on:
  push:
    branches:
      - 'main'  # Run on push to main branch only
      - 'develop'  # Run on push to develop branch
  pull_request:
    branches:
      - 'main'  # Run on pull requests to main branch
  workflow_dispatch:  # Manual trigger

# Define environment variables needed for the application
env:
  # Basic application settings
  ENVIRONMENT: test
  APP_NAME: rag-app
  DEBUG: "true"
  
  # Database connection settings (for testing only)
  POSTGRES_HOST: localhost
  POSTGRES_DB: test_db
  POSTGRES_USER: test_user
  POSTGRES_PASSWORD: test_password
  POSTGRES_PORT: 5432
  
  # API endpoints and paths
  ARXIV_API_URL: https://export.arxiv.org/api/query
  DATA_PATH: ./data
  
  # Model generation parameters
  TEMPERATURE: "0.7"
  TOP_P: "0.9"
  MAX_TOKENS: "1000"
  
  # Opik API settings (for AI model evaluation)
  OPIK_API_KEY: ${{ secrets.OPIK_API_KEY }}
  OPIK_WORKSPACE: ${{ secrets.OPIK_WORKSPACE }}
  OPIK_ENVIRONMENT: test
  OPIK_PROJECT_NAME: rag-app-test
  
  # Poetry version to use
  POETRY_VERSION: "1.8.2"

jobs:
  ci:
    name: CI Pipeline
    runs-on: ubuntu-latest
    services:
      postgres:
        image: ankane/pgvector:latest
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      # Step 1: Check out the code
      - name: Checkout code
        uses: actions/checkout@v4
      
      # Step 2: Set up Python environment
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
          
      # Step 3: Cache Poetry installation and dependencies
      - name: Cache Poetry and dependencies
        uses: actions/cache@v3
        with:
          path: |
            ~/.local
            ~/.cache/pypoetry
            ./rag-app/.venv
          key: poetry-${{ runner.os }}-${{ env.POETRY_VERSION }}-${{ hashFiles('**/poetry.lock') }}
          restore-keys: |
            poetry-${{ runner.os }}-${{ env.POETRY_VERSION }}-
          
      # Step 4: Install Poetry package manager
      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 - --version ${{ env.POETRY_VERSION }}
          poetry config virtualenvs.create true
          poetry config virtualenvs.in-project true
          
      # Step 5: Install project dependencies
      - name: Install dependencies
        working-directory: ./rag-app
        run: |
          echo "Installing dependencies..."
          poetry install --no-interaction
          echo "Installation complete!"
      
      # Step 6: Initialize database and run tests
      - name: Initialize database and run tests
        working-directory: ./rag-app
        run: |
          # Wait for PostgreSQL to be ready
          echo "Waiting for PostgreSQL to be ready..."
          until poetry run python -c "import psycopg2; conn = psycopg2.connect(dbname='test_db', user='test_user', password='test_password', host='localhost'); conn.close()" 2>/dev/null; do
            echo "PostgreSQL is unavailable - sleeping"
            sleep 1
          done
          echo "PostgreSQL is up - executing tests"
          
          # Run tests with coverage
          poetry run pytest tests/ -v --junitxml=test-results.xml --cov=server --cov-report=xml
          
      # Step 7: Upload test results and coverage as artifacts
      - name: Upload test results and coverage
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: |
            rag-app/test-results.xml
            rag-app/coverage.xml
```

## 4. Streamlit App Improvements

### 4.1 Enhanced User Interface and Functionality

**Why**: The original Streamlit app was basic and lacked important features like parameter control, timestamps, and proper styling. The improved version provides a more professional and user-friendly experience.

The Streamlit app in `rag-app-aws/client/streamlit_app.py` was completely refactored with the following improvements:

#### 4.1.1 Modular Code Structure

The new app uses a modular approach with separate functions for different components:

```python
def apply_custom_css():
    # Custom CSS styling
    ...

def query_fastapi(query, top_k=5, max_tokens=200, temperature=0.7):
    # API query logic
    ...

def display_header():
    # Header display logic
    ...

def display_sidebar():
    # Sidebar with controls
    ...

def display_chat_message(message, role):
    # Chat message display logic
    ...

def main():
    # Main application flow
    ...
```

This modular structure makes the code more maintainable, easier to understand, and allows for better separation of concerns.

#### 4.1.2 Enhanced UI with Custom CSS

The new app includes comprehensive custom CSS styling for a more professional look:

```python
def apply_custom_css():
    st.markdown("""
    <style>
    /* Main container styling */
    .main .block-container {
        max-width: 1000px;
        padding-top: 2rem;
    }
    
    /* Header styling */
    .header-container {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
        background-color: #f0f2f6;
        border-radius: 10px;
    }
    
    /* Chat message styling */
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* User message styling */
    .stChatMessage[data-testid="stChatMessage"][data-role="user"] {
        background-color: #e6f3ff;
    }
    
    /* Assistant message styling */
    .stChatMessage[data-testid="stChatMessage"][data-role="assistant"] {
        background-color: #f0f2f6;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f0f2f6;
    }
    
    /* Button styling */
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    /* Input field styling */
    .stTextInput input {
        border-radius: 5px;
        border: 1px solid #ccc;
    }
    
    /* Error message styling */
    .error-message {
        color: #d32f2f;
        font-weight: bold;
        padding: 0.5rem;
        border-radius: 5px;
        background-color: #ffebee;
    }
    </style>
    """, unsafe_allow_html=True)
```

This styling improves the visual appeal and usability of the app with:
- Consistent color scheme
- Better spacing and layout
- Distinct styling for user and assistant messages
- Improved button and input field appearance
- Error message highlighting

#### 4.1.3 Interactive Parameter Controls

The new app adds a sidebar with interactive controls for model parameters:

```python
def display_sidebar():
    """Display sidebar with controls and information."""
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Model parameters
        st.subheader("Model Parameters")
        top_k = st.slider("Top K", min_value=1, max_value=10, value=5, 
                          help="Number of top results to consider")
        st.session_state["top_k"] = top_k
        
        max_tokens = st.slider("Max Tokens", min_value=50, max_value=500, value=200, 
                              help="Maximum number of tokens in the response")
        st.session_state["max_tokens"] = max_tokens
        
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, 
                               help="Higher values make the output more random, lower values more deterministic")
        st.session_state["temperature"] = temperature
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state["messages"] = []
            st.rerun()
```

These controls allow users to:
- Adjust the number of top results to consider (`top_k`)
- Control the maximum length of the response (`max_tokens`)
- Fine-tune the randomness of the model's output (`temperature`)
- Clear the chat history with a single click

#### 4.1.4 Message Timestamps and Improved Chat Display

The new app adds timestamps to messages and improves the chat display:

```python
def display_chat_message(message, role):
    """Display a chat message with timestamp."""
    with st.chat_message(role):
        st.markdown(message["content"])
        # Add timestamp if available
        if "timestamp" in message:
            st.caption(f"Sent at {message['timestamp']}")
```

And in the main function:

```python
# Display user message
timestamp = datetime.now().strftime("%H:%M:%S")
user_message = {"role": "user", "content": query, "timestamp": timestamp}
st.session_state["messages"].append(user_message)
display_chat_message(user_message, "user")

# ...

# Display bot response
timestamp = datetime.now().strftime("%H:%M:%S")
assistant_message = {"role": "assistant", "content": answer, "timestamp": timestamp}
st.session_state["messages"].append(assistant_message)
display_chat_message(assistant_message, "assistant")
```

This provides:
- Timestamps for each message
- Consistent message display through a dedicated function
- Better visual separation between user and assistant messages

#### 4.1.5 Loading Indicator

The new app adds a loading spinner while waiting for the API response:

```python
# Show loading spinner while waiting for response
with st.spinner("Thinking..."):
    # Get response from FastAPI backend
    response = query_fastapi(query, top_k, max_tokens, temperature)
```

This provides visual feedback to users that the app is processing their request, improving the user experience.

#### 4.1.6 Proper Page Configuration

The new app ensures that `st.set_page_config()` is called first, as required by Streamlit:

```python
def main():
    # Set page configuration - MUST BE THE FIRST STREAMLIT COMMAND
    st.set_page_config(
        page_title="AI Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Rest of the code...
```

This prevents the `StreamlitSetPageConfigMustBeFirstCommandError` error that can occur if other Streamlit commands are called before `set_page_config()`.

### 4.2 Key Improvements Summary

| Feature | Old App | New App | Benefit |
|---------|---------|---------|---------|
| Code Structure | Monolithic | Modular | Better maintainability and readability |
| UI Styling | Basic | Custom CSS | More professional appearance |
| Parameter Controls | None | Interactive sliders | User control over model behavior |
| Message Timestamps | None | Added | Better conversation tracking |
| Loading Indicator | None | Added | Improved user feedback |
| Chat History Management | Basic | Clear button | Better user control |
| Error Handling | Basic | Improved | Better error visibility |
| Page Configuration | Incorrect order | Correct order | Prevents Streamlit errors |

These improvements make the Streamlit app more professional, user-friendly, and feature-rich, providing a better experience for users interacting with the RAG system.

