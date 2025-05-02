#!/bin/bash

# This script helps build the Docker image when behind Zscaler
# It sets up the necessary environment variables and options for Docker build

# Set environment variables for Docker build
export DOCKER_BUILDKIT=1
export DOCKER_CLIENT_TIMEOUT=120
export COMPOSE_HTTP_TIMEOUT=120

# Build the Docker image with specific options to handle SSL issues
docker build \
  --network=host \
  --build-arg HTTP_PROXY=$http_proxy \
  --build-arg HTTPS_PROXY=$https_proxy \
  --build-arg NO_PROXY=localhost,127.0.0.1 \
  -f pgvector2.Dockerfile \
  -t postgres-pgvector .

# Run the container
docker run -d \
  -p 5432:5432 \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_PASSWORD=mypassword \
  -e POSTGRES_DB=mydb \
  --name postgres-pgvector \
  postgres-pgvector

echo "PostgreSQL with pgvector extension is now running on port 5432" 