# RAG Implementation Guide

This guide explains how our Retrieval-Augmented Generation (RAG) pipeline works. It's written for beginners and assumes basic knowledge of Python and APIs.

## Table of Contents
1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Components](#components)
4. [How It Works](#how-it-works)
5. [Setup and Installation](#setup-and-installation)
6. [Usage](#usage)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)

## Overview

This document provides a detailed explanation of the Retrieval-Augmented Generation (RAG) implementation in this project. The RAG system combines document retrieval with language model generation to provide accurate, context-aware responses to user queries.

## Project Structure

The project is organized as follows:

```
rag-app/
├── server/                 # FastAPI backend server
│   ├── src/                # Source code
│   │   ├── controllers/    # API endpoints
│   │   ├── ingestion/      # Data ingestion pipeline
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   ├── config.py       # Configuration settings
│   │   └── main.py         # Application entry point
│   ├── tests/              # Test suite
│   ├── Dockerfile          # Container definition
│   └── requirements.txt    # Python dependencies
├── client/                 # Streamlit frontend
│   └── streamlit_app.py    # Streamlit application
├── data/                   # Data storage
├── Makefile                # Build and run commands
└── README.md               # Project documentation
```

## Container Structure

The project uses a containerized development environment to ensure consistency across different development machines and simplify the setup process. This approach offers several key benefits:

### Why Containerization is Necessary

1. **Environment Consistency**: Containers ensure that all developers work with the same dependencies, versions, and configurations, eliminating "it works on my machine" problems.

2. **Isolation**: The development environment is isolated from the host system, preventing conflicts with other projects or system-wide dependencies.

3. **Reproducibility**: New team members can quickly get started without manually installing numerous dependencies.

4. **Security**: Sensitive credentials and configurations can be managed securely within the container environment.

### Container Implementation

The container structure consists of two main components:

1. **Dockerfile** (`.devcontainer/Dockerfile`):
   - Based on the official Microsoft Python dev container image
   - Installs AWS CLI with architecture detection (supports both x86_64 and ARM)
   - Configures SSL certificates for secure connections
   - Sets up Python dependencies from requirements.txt
   - Configures Git for safe directory access

2. **Dev Container Configuration** (`.devcontainer/devcontainer.json`):
   - Defines the development container settings
   - Configures VS Code extensions (including Jupyter support)
   - Sets up GitHub CLI integration
   - Mounts the user's Git configuration for seamless version control
   - Configures the Python environment with Poetry for dependency management

This containerized approach allows developers to work in a consistent environment regardless of their local setup, making it easier to focus on development rather than environment configuration.

## GitHub Workflows

The project uses GitHub Actions workflows to automate testing, validation, and deployment processes. These workflows ensure code quality and reliability throughout the development lifecycle.

### CI Initialization Workflow

The `ci-initialise.yml` workflow runs automated tests whenever code is pushed to any branch:

1. **Environment Setup**:
   - Runs on Ubuntu latest
   - Sets up a PostgreSQL database with pgvector extension for vector similarity search
   - Configures environment variables for testing

2. **Dependency Management**:
   - Uses Poetry for Python dependency management
   - Caches Poetry installation and dependencies for faster workflow execution
   - Installs project dependencies in an isolated environment

3. **Testing Process**:
   - Runs the test suite using pytest
   - Generates XML test reports
   - Uploads test results as artifacts for later analysis

This workflow ensures that code changes don't introduce regressions and maintains the quality of the codebase.

### Secrets Verification Workflow

The `verify-secrets.yml` workflow validates that all required secrets are properly configured:

1. **Manual Trigger**: This workflow can be manually triggered to verify secrets at any time.

2. **Secret Validation**: Checks for the presence of critical secrets:
   - Database credentials (POSTGRES_USER, POSTGRES_PASSWORD)
   - API keys (OPIK_API_KEY, OPENAI_API_KEY)
   - Workspace configurations (OPIK_WORKSPACE, OPIK_PROJECT_NAME)

3. **Verification Reporting**: Provides clear feedback on which secrets are properly configured.

This workflow helps prevent deployment issues caused by missing or incorrectly configured secrets.

## Main Components

### 1. Data Ingestion Pipeline

The ingestion pipeline (`server/src/ingestion/`) is responsible for processing documents and preparing them for retrieval:

- **Text Chunking**: Breaks documents into smaller, manageable chunks for better retrieval
- **Embedding Generation**: Creates vector embeddings using SentenceTransformer
- **Database Storage**: Stores document chunks and embeddings in PostgreSQL with pgvector

### 2. Retrieval Service

The retrieval service (`server/src/services/retrieval_service.py`) finds relevant documents for a given query:

- **Query Embedding**: Converts user queries into vector embeddings
- **Similarity Search**: Uses cosine similarity to find the most relevant document chunks
- **Database Integration**: Leverages pgvector for efficient vector similarity search

### 3. Generation Service

The generation service (`server/src/services/generation_service.py`) creates responses based on retrieved documents:

- **Context Preparation**: Formats retrieved documents for the language model
- **LLM Integration**: Currently uses OpenAI's API (with plans to transition to AWS Bedrock)
- **Response Generation**: Creates coherent answers based on the retrieved context

### 4. API Controllers

The API controllers (`server/src/controllers/`) expose endpoints for interacting with the RAG system:

- **Retrieval Endpoint**: Returns relevant document chunks for a query
- **Generation Endpoint**: Generates responses based on retrieved documents
- **Health Check**: Monitors system status

## How It Works

### Step 1: Document Processing

1. Documents are read from JSON files
2. Text is chunked into smaller segments
3. Embeddings are generated for each chunk using SentenceTransformer
4. Chunks and embeddings are stored in PostgreSQL with pgvector

### Step 2: Query Processing

1. User submits a query through the API
2. The query is converted to an embedding using the same SentenceTransformer model
3. The system retrieves the top K most similar document chunks using cosine similarity

### Step 3: Response Generation

1. Retrieved document chunks are formatted as context
2. The context and query are sent to the language model (currently OpenAI)
3. The model generates a response based on the provided context
4. The response is returned to the user

## Setup and Installation

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL with pgvector extension
- OpenAI API key (for generation)

### Environment Setup

1. Clone the repository
2. Create a `.env` file with the following variables:
   ```
   POSTGRES_HOST=localhost
   POSTGRES_DB=rag_db
   POSTGRES_USER=your_username
   POSTGRES_PASSWORD=your_password
   POSTGRES_PORT=5432
   OPENAI_API_KEY=your_openai_api_key
   ```

3. Start the development container:
   ```bash
   # From the project root
   code .
   # VS Code will prompt to reopen in container - accept this
   ```

4. Install dependencies:
   ```bash
   # Inside the container
   cd rag-app
   make install
   ```

5. Build the database:
   ```bash
   # Inside the container
   make build-db
   ```

6. Run the ingestion pipeline:
   ```bash
   # Inside the container
   make run-ingestion
   ```

7. Start the application:
   ```bash
   # Inside the container
   make run-app
   ```

8. In a new terminal, start the client:
   ```bash
   # Inside the container
   make run-client
   ```

## Usage

### API Endpoints

1. **Retrieve Documents**:
   ```
   GET /api/retrieve?query=your_query&top_k=5
   ```
   Returns the top K most relevant document chunks for the given query.

2. **Generate Response**:
   ```
   POST /api/generate
   {
     "query": "your_query",
     "top_k": 5,
     "max_tokens": 1000,
     "temperature": 0.7
   }
   ```
   Generates a response based on the retrieved documents.

### Streamlit Interface

The Streamlit interface provides a user-friendly way to interact with the RAG system:
1. Enter your query in the text input
2. View the generated response
3. See the retrieved document chunks that informed the response

## Configuration

The system can be configured through environment variables and YAML files:

### Environment Variables

The application uses environment variables for most configuration settings, which are loaded through the `Settings` class in `config.py`. These include:

- **Database connection settings**: `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`
- **API endpoints and paths**: `ARXIV_API_URL`, `DATA_PATH`
- **Model parameters**: `TEMPERATURE`, `TOP_P`, `MAX_TOKENS`
- **API keys**: `OPENAI_API_KEY`, `OPIK_API_KEY`
- **Workspace configurations**: `OPIK_WORKSPACE`, `OPIK_PROJECT_NAME`

These variables can be set in a `.env` file or directly in the environment.

### YAML Configuration

The project includes a YAML configuration file at `rag-app/server/config/rag.yaml` that contains specific settings for the RAG pipeline:

```yaml
retrieval:
  top_k: 5  # Number of documents to retrieve
  re_rank: false  # Re-rank documents after retrieval

query_expansion:
  enabled: true
  method: "llm"  # Options: "llm", "synonym", "embedding"
  max_expansion_terms: 3

summarization:
  enabled: false
  method: "density"  # Options: "density", "standard"
  max_iterations: 2

generation:
  model: "tinyllama"
  temperature: 0.7
```

This configuration file is loaded by the `ConfigLoader` class in `config_loader.py`, which provides methods to access these settings throughout the application. The YAML configuration allows for more structured and hierarchical configuration compared to environment variables, making it easier to manage complex settings.

The configuration includes:

1. **Retrieval Settings**: Controls how many documents to retrieve and whether to re-rank them
2. **Query Expansion**: Enables and configures query expansion techniques to improve retrieval
3. **Summarization**: Controls document summarization options
4. **Generation**: Specifies the model to use and generation parameters

This YAML-based configuration approach provides flexibility and allows for easy modification of the RAG pipeline's behavior without changing code.

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Verify PostgreSQL is running
   - Check connection parameters in `.env`
   - Ensure pgvector extension is installed

2. **Embedding Generation Failures**:
   - Check available memory
   - Verify SentenceTransformer model is downloaded
   - Ensure input text is properly formatted

3. **LLM API Issues**:
   - Verify API key is valid
   - Check network connectivity
   - Ensure request parameters are within limits

## Next Steps

1. **AWS Bedrock Integration**:
   - Replace OpenAI with AWS Bedrock for generation
   - Implement AWS Bedrock embeddings
   - Add AWS-specific configuration

2. **Performance Optimization**:
   - Implement caching for frequently accessed documents
   - Optimize database queries
   - Add batch processing for large document sets

3. **Enhanced Retrieval**:
   - Implement hybrid search (keyword + semantic)
   - Add document filtering capabilities
   - Improve chunk selection strategies 