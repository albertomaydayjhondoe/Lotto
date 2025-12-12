FROM mcr.microsoft.com/devcontainers/base:ubuntu

# Install basic dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    build-essential \
    curl \
    git \
    postgresql-client \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*
