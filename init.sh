#!/bin/bash

# Etcd Helper Service Initialization Script
# This script sets up the environment for the etcdHelper service.
# It checks requirements, installs dependencies, and configures environment variables.

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Etcd Helper Service Initialization...${NC}"

# 1. Check Node.js and npm
echo -e "\n${YELLOW}[1/3] Checking environment requirements...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed.${NC}"
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed.${NC}"
    exit 1
fi

NODE_VERSION=$(node -v)
NPM_VERSION=$(npm -v)
echo "Node.js version: $NODE_VERSION"
echo "npm version: $NPM_VERSION"

# 2. Install Dependencies
echo -e "\n${YELLOW}[2/3] Installing dependencies...${NC}"
if [ -f "package-lock.json" ]; then
    npm ci
else
    npm install
fi

# 3. Environment Configuration
echo -e "\n${YELLOW}[3/3] Configuring environment...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo -e "${GREEN}Created .env file. Please review it and update configuration if necessary.${NC}"
    else
        echo -e "${RED}Warning: .env.example not found. Skipping .env creation.${NC}"
    fi
else
    echo ".env file already exists. Skipping creation."
fi

echo -e "\n${GREEN}Initialization complete!${NC}"
echo -e "You can now start the service with: ${YELLOW}node index.js${NC}"
