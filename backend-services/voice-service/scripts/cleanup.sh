#!/bin/bash
# Script to clean up temporary files

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Navigate to voice service directory
cd "$(dirname "$0")/.." || exit 1

echo -e "${BLUE}Cleaning up temporary files...${NC}"

# Remove Python cache files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete
find . -type f -name ".DS_Store" -delete
find . -type d -name ".pytest_cache" -exec rm -rf {} +
find . -type d -name ".coverage" -exec rm -rf {} +
find . -type d -name "htmlcov" -exec rm -rf {} +

# Clean logs directory but keep the directory itself
rm -f logs/*.log*

echo -e "${GREEN}Cleanup complete!${NC}"
