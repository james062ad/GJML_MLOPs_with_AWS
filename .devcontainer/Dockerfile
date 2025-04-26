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
