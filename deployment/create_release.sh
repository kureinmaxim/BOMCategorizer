#!/bin/bash
# Script to create GitHub release with DMG file attachment for macOS
# Usage: ./create_release.sh -t "your_github_token" -v "4.4.2"

set -e  # Exit on error

# Default values
VERSION="4.4.2"
REPO="kureinmaxim/BOMCategorizer"
SETUP_FILE=""
TOKEN=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print usage
usage() {
    echo "Usage: $0 -t TOKEN [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --token TOKEN       GitHub Personal Access Token (required)"
    echo "  -v, --version VERSION    Version number (default: 4.4.2)"
    echo "  -r, --repo REPO          Repository in format owner/repo (default: kureinmaxim/BOMCategorizer)"
    echo "  -f, --file FILE          DMG file name (default: BOMCategorizer-{VERSION}-macOS-Modern.dmg)"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -t \"ghp_xxxxxxxxxxxxxxxxxxxx\""
    echo "  $0 -t \"ghp_xxxxxxxxxxxxxxxxxxxx\" -v \"4.4.2\""
    echo "  $0 -t \"ghp_xxxxxxxxxxxxxxxxxxxx\" -v \"4.4.2\" -f \"custom.dmg\""
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--token)
            TOKEN="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -r|--repo)
            REPO="$2"
            shift 2
            ;;
        -f|--file)
            SETUP_FILE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
    esac
done

# Check if token is provided
if [ -z "$TOKEN" ]; then
    echo -e "${RED}ERROR: Token is required!${NC}"
    usage
fi

# Set default file name if not provided
if [ -z "$SETUP_FILE" ]; then
    SETUP_FILE="BOMCategorizer-${VERSION}-macOS-Modern.dmg"
fi

TAG="v${VERSION}"
RELEASE_NAME="BOM Categorizer Modern Edition ${VERSION}"
RELEASE_BODY="BOM Categorizer Modern Edition ${VERSION}

macOS installer file (.dmg)"

echo -e "${CYAN}Creating release ${TAG} for ${REPO}...${NC}"

# Check if file exists
if [ ! -f "$SETUP_FILE" ]; then
    echo -e "${RED}ERROR: File ${SETUP_FILE} not found!${NC}"
    exit 1
fi

# Get file size in MB
FILE_SIZE=$(du -h "$SETUP_FILE" | cut -f1)
echo -e "${YELLOW}File size: ${FILE_SIZE}${NC}"

# Create release via GitHub API
echo -e "${CYAN}Sending request to create release...${NC}"

CREATE_URL="https://api.github.com/repos/${REPO}/releases"

# Create release JSON payload using jq or Python for proper JSON encoding
if command -v jq &> /dev/null; then
    # Use jq for proper JSON encoding (handles newlines, quotes, etc. automatically)
    RELEASE_JSON=$(jq -n \
        --arg tag "$TAG" \
        --arg name "$RELEASE_NAME" \
        --arg body "$RELEASE_BODY" \
        '{tag_name: $tag, name: $name, body: $body, draft: false, prerelease: false}')
elif command -v python3 &> /dev/null; then
    # Use Python3 for proper JSON encoding (more reliable than manual escaping)
    RELEASE_JSON=$(python3 <<PYTHON_SCRIPT
import json
import sys

tag = '$TAG'
name = '''$RELEASE_NAME'''
body = '''$RELEASE_BODY'''

data = {
    'tag_name': tag,
    'name': name,
    'body': body,
    'draft': False,
    'prerelease': False
}

print(json.dumps(data, ensure_ascii=False))
PYTHON_SCRIPT
)
else
    # Fallback: use simple body without newlines to avoid JSON parsing issues
    echo -e "${YELLOW}Warning: jq or python3 not found. Using simplified release body.${NC}"
    echo -e "${YELLOW}Install jq for better formatting: brew install jq${NC}"
    SIMPLE_BODY="BOM Categorizer Modern Edition ${VERSION} - macOS installer file (.dmg)"
    RELEASE_JSON=$(cat <<EOF
{
  "tag_name": "${TAG}",
  "name": "${RELEASE_NAME}",
  "body": "${SIMPLE_BODY}",
  "draft": false,
  "prerelease": false
}
EOF
)
fi

# Create release
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Authorization: token ${TOKEN}" \
    -H "Accept: application/vnd.github.v3+json" \
    -H "Content-Type: application/json" \
    -d "${RELEASE_JSON}" \
    "${CREATE_URL}")

# Extract HTTP status code (last line)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

# Check if release was created successfully
if [ "$HTTP_CODE" -eq 201 ]; then
    echo -e "${GREEN}Release created successfully!${NC}"
    
    # Extract release ID and upload URL from response
    RELEASE_ID=$(echo "$RESPONSE_BODY" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    UPLOAD_URL=$(echo "$RESPONSE_BODY" | grep -o '"upload_url":"[^"]*' | cut -d'"' -f4 | sed 's/{?name,label}/?name='$(basename "$SETUP_FILE")'/')
    HTML_URL=$(echo "$RESPONSE_BODY" | grep -o '"html_url":"[^"]*' | cut -d'"' -f4)
    
    echo -e "${CYAN}Release ID: ${RELEASE_ID}${NC}"
    
    # Upload file
    echo -e "${CYAN}Uploading file ${SETUP_FILE}...${NC}"
    
    # Get file MIME type
    MIME_TYPE=$(file --mime-type -b "$SETUP_FILE")
    if [ "$MIME_TYPE" = "application/octet-stream" ] || [ -z "$MIME_TYPE" ]; then
        # For DMG files, use application/x-apple-diskimage
        MIME_TYPE="application/x-apple-diskimage"
    fi
    
    UPLOAD_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Authorization: token ${TOKEN}" \
        -H "Content-Type: ${MIME_TYPE}" \
        --data-binary "@${SETUP_FILE}" \
        "${UPLOAD_URL}")
    
    UPLOAD_HTTP_CODE=$(echo "$UPLOAD_RESPONSE" | tail -n1)
    UPLOAD_BODY=$(echo "$UPLOAD_RESPONSE" | sed '$d')
    
    if [ "$UPLOAD_HTTP_CODE" -eq 201 ]; then
        echo -e "${GREEN}File uploaded successfully!${NC}"
        echo -e "${CYAN}Release URL: ${HTML_URL}${NC}"
    else
        echo -e "${RED}ERROR uploading file:${NC}"
        echo "$UPLOAD_BODY" | head -20
        exit 1
    fi
    
elif [ "$HTTP_CODE" -eq 422 ]; then
    echo -e "${YELLOW}Release already exists (HTTP 422).${NC}"
    echo -e "${YELLOW}You can:${NC}"
    echo -e "  1. Use 'gh release upload ${TAG} ${SETUP_FILE} --clobber' to update the file"
    echo -e "  2. Use './upload_to_existing_release.sh -t \"ваш_токен\" -v \"${VERSION}\"' to update the file"
    echo -e "  3. Delete the existing release and try again"
    echo -e "  4. Update the release manually via web interface"
    exit 1
else
    echo -e "${RED}ERROR creating release (HTTP ${HTTP_CODE}):${NC}"
    echo "$RESPONSE_BODY" | head -20
    exit 1
fi

