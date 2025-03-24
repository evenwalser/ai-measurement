#!/bin/bash

# Start Testing Environment for Body Measurement API
# This script sets up and starts all required services

# Set up color formatting
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================================${NC}"
echo -e "${BLUE}       Starting Body Measurement API Test Environment    ${NC}"
echo -e "${BLUE}========================================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo -e "${RED}Error: Docker is not running. Please start Docker and try again.${NC}"
  exit 1
fi

# Create necessary directories if they don't exist
if [ ! -d "test-images" ]; then
  echo -e "${YELLOW}Creating test-images directory...${NC}"
  mkdir -p test-images
fi

if [ ! -d "test-results" ]; then
  echo -e "${YELLOW}Creating test-results directory...${NC}"
  mkdir -p test-results
fi

# Check if containers are already running
if docker ps | grep -q "body-measurement-api"; then
  echo -e "${YELLOW}Body Measurement API containers are already running.${NC}"
  echo -e "${YELLOW}Stopping existing containers...${NC}"
  docker-compose down
fi

# Start the API services
echo -e "${YELLOW}Starting Body Measurement API services...${NC}"
docker-compose up -d

# Wait for the API to be ready
echo -e "${YELLOW}Waiting for API to start...${NC}"
attempt=1
max_attempts=10
while ! curl -s http://localhost:8080/api/v1/status.php > /dev/null; do
  if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}Error: Failed to start the API after $max_attempts attempts.${NC}"
    echo -e "${RED}Check the Docker logs using 'docker-compose logs' for more details.${NC}"
    exit 1
  fi
  echo -e "${YELLOW}Attempt $attempt/$max_attempts - waiting for API to start...${NC}"
  sleep 3
  ((attempt++))
done

# Check Python service
echo -e "${YELLOW}Checking Python measurement service...${NC}"
if docker ps | grep -q "body-measurement-python"; then
  echo -e "${GREEN}Python measurement service is running.${NC}"
else
  echo -e "${RED}Warning: Python measurement service is not running.${NC}"
  echo -e "${YELLOW}Starting Python service...${NC}"
  docker-compose up -d python
  sleep 3
  
  if docker ps | grep -q "body-measurement-python"; then
    echo -e "${GREEN}Python measurement service is now running.${NC}"
  else
    echo -e "${RED}Error: Failed to start Python measurement service.${NC}"
    echo -e "${RED}Check the Docker logs using 'docker-compose logs python' for more details.${NC}"
    exit 1
  fi
fi

# Open the testing interface in the default browser
echo -e "${YELLOW}Opening testing interface in browser...${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
  open http://localhost:8080/testing-frontend/
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
  xdg-open http://localhost:8080/testing-frontend/ &> /dev/null
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
  start http://localhost:8080/testing-frontend/
else
  echo -e "${YELLOW}Please open http://localhost:8080/testing-frontend/ in your browser.${NC}"
fi

echo ""
echo -e "${GREEN}Body Measurement API testing environment is now running!${NC}"
echo -e "${GREEN}API URL: http://localhost:8080/api/v1/measurements${NC}"
echo -e "${GREEN}Testing interface: http://localhost:8080/testing-frontend/${NC}"
echo ""
echo -e "${BLUE}Available commands:${NC}"
echo -e "  ./test-calibration.sh - Run automated tests on all calibration methods"
echo -e "  docker-compose logs - View logs from all services"
echo -e "  docker-compose down - Stop all services"
echo ""
echo -e "${BLUE}========================================================${NC}" 