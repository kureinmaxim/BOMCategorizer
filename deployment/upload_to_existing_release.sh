#!/bin/bash
# Script to upload files to existing GitHub release (supports multiple files)
# Usage: ./upload_to_existing_release.sh -t "your_github_token" -v "4.4.5" -f "file1.dmg" -f "file2.exe"

# Don't exit on error - we want to continue uploading other files if one fails
set +e

# Default values
VERSION="4.4.2"
REPO="kureinmaxim/BOMCategorizer"
FILES=()  # Array to store multiple files
TOKEN=""
AUTO_DETECT=true  # Auto-detect both .dmg and .exe files

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
    echo "  -f, --file FILE          File to upload (can be used multiple times for multiple files)"
    echo "  -a, --auto               Auto-detect .dmg and .exe files for version (default: enabled)"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -t \"ghp_xxx\" -v \"4.4.5\""
    echo "    # Auto-detects BOMCategorizer-4.4.5-macOS-Modern.dmg and BOMCategorizerModernSetup.exe"
    echo ""
    echo "  $0 -t \"ghp_xxx\" -v \"4.4.5\" -f \"file1.dmg\" -f \"file2.exe\""
    echo "    # Uploads specific files"
    echo ""
    echo "  $0 -t \"ghp_xxx\" -v \"4.4.5\" -f \"custom.dmg\" --no-auto"
    echo "    # Uploads only custom.dmg, no auto-detection"
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
            FILES+=("$2")
            AUTO_DETECT=false
            shift 2
            ;;
        -a|--auto)
            AUTO_DETECT=true
            shift
            ;;
        --no-auto)
            AUTO_DETECT=false
            shift
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

# Auto-detect files if no files specified and auto-detect is enabled
if [ ${#FILES[@]} -eq 0 ] && [ "$AUTO_DETECT" = true ]; then
    MACOS_FILE="BOMCategorizer-${VERSION}-macOS-Modern.dmg"
    WINDOWS_FILE="BOMCategorizerModernSetup.exe"
    
    if [ -f "$MACOS_FILE" ]; then
        FILES+=("$MACOS_FILE")
        echo -e "${CYAN}Auto-detected: ${MACOS_FILE}${NC}"
    fi
    
    if [ -f "$WINDOWS_FILE" ]; then
        FILES+=("$WINDOWS_FILE")
        echo -e "${CYAN}Auto-detected: ${WINDOWS_FILE}${NC}"
    fi
    
    if [ ${#FILES[@]} -eq 0 ]; then
        echo -e "${YELLOW}No files auto-detected. Use -f to specify files manually.${NC}"
        exit 1
    fi
fi

# Check if we have any files to upload
if [ ${#FILES[@]} -eq 0 ]; then
    echo -e "${RED}ERROR: No files specified!${NC}"
    usage
fi

TAG="v${VERSION}"

echo -e "${CYAN}Uploading ${#FILES[@]} file(s) to existing release ${TAG} for ${REPO}...${NC}"

# Check if all files exist
for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}ERROR: File ${file} not found!${NC}"
        exit 1
    fi
done

# Show file sizes
for file in "${FILES[@]}"; do
    FILE_SIZE=$(du -h "$file" | cut -f1)
    echo -e "${YELLOW}  ${file}: ${FILE_SIZE}${NC}"
done
echo ""

# Get existing release
echo -e "${CYAN}Getting release info...${NC}"

GET_RELEASE_URL="https://api.github.com/repos/${REPO}/releases/tags/${TAG}"

RESPONSE=$(curl -s -w "\n%{http_code}" -X GET \
    -H "Authorization: token ${TOKEN}" \
    -H "Accept: application/vnd.github.v3+json" \
    "${GET_RELEASE_URL}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -ne 200 ]; then
    echo -e "${RED}ERROR: Release ${TAG} not found (HTTP ${HTTP_CODE})${NC}"
    echo "$RESPONSE_BODY" | head -20
    exit 1
fi

# Extract release ID and base upload URL (without filename)
# Use jq if available for better JSON parsing
if command -v jq &> /dev/null; then
    RELEASE_ID=$(echo "$RESPONSE_BODY" | jq -r '.id')
    BASE_UPLOAD_URL=$(echo "$RESPONSE_BODY" | jq -r '.upload_url' | sed 's/{?name,label}//')
    HTML_URL=$(echo "$RESPONSE_BODY" | jq -r '.html_url')
else
    # Fallback to grep parsing
    RELEASE_ID=$(echo "$RESPONSE_BODY" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2 | tr -d ' ')
    BASE_UPLOAD_URL=$(echo "$RESPONSE_BODY" | grep -o '"upload_url":"[^"]*' | cut -d'"' -f4 | sed 's/{?name,label}//')
    HTML_URL=$(echo "$RESPONSE_BODY" | grep -o '"html_url":"[^"]*' | cut -d'"' -f4)
fi

if [ -z "$RELEASE_ID" ] || [ -z "$BASE_UPLOAD_URL" ]; then
    echo -e "${RED}ERROR: Could not parse release information from API response${NC}"
    echo -e "${YELLOW}Response body:${NC}"
    echo "$RESPONSE_BODY" | head -20
    exit 1
fi

echo -e "${GREEN}Found release! ID: ${RELEASE_ID}${NC}"
echo ""

# Upload each file
UPLOADED_COUNT=0
FAILED_COUNT=0

for SETUP_FILE in "${FILES[@]}"; do
    ASSET_NAME=$(basename "$SETUP_FILE")
    echo -e "${CYAN}Processing: ${ASSET_NAME}...${NC}"
    
    # Check if asset already exists
    if command -v jq &> /dev/null; then
        EXISTING_ASSET=$(echo "$RESPONSE_BODY" | jq -r ".assets[] | select(.name == \"${ASSET_NAME}\") | .id")
    else
        EXISTING_ASSET=$(echo "$RESPONSE_BODY" | grep -o "\"name\":\"${ASSET_NAME}\"[^}]*\"id\":[0-9]*" | grep -o '"id":[0-9]*' | cut -d':' -f2 | tr -d ' ')
    fi
    
    if [ -n "$EXISTING_ASSET" ]; then
        echo -e "${YELLOW}  Asset ${ASSET_NAME} already exists. Deleting old version...${NC}"
        
        DELETE_URL="https://api.github.com/repos/${REPO}/releases/assets/${EXISTING_ASSET}"
        DELETE_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE \
            -H "Authorization: token ${TOKEN}" \
            -H "Accept: application/vnd.github.v3+json" \
            "${DELETE_URL}")
        
        DELETE_HTTP_CODE=$(echo "$DELETE_RESPONSE" | tail -n1)
        
        if [ "$DELETE_HTTP_CODE" -eq 204 ]; then
            echo -e "${GREEN}  Old asset deleted.${NC}"
        else
            echo -e "${YELLOW}  Warning: Could not delete old asset (HTTP ${DELETE_HTTP_CODE}), continuing anyway...${NC}"
        fi
    fi
    
    # Upload file
    echo -e "${CYAN}  Uploading ${ASSET_NAME}...${NC}"
    
    # Get file MIME type
    MIME_TYPE=$(file --mime-type -b "$SETUP_FILE")
    if [ "$MIME_TYPE" = "application/octet-stream" ] || [ -z "$MIME_TYPE" ]; then
        # Detect file type by extension
        if [[ "$SETUP_FILE" == *.dmg ]]; then
            MIME_TYPE="application/x-apple-diskimage"
        elif [[ "$SETUP_FILE" == *.exe ]]; then
            MIME_TYPE="application/x-msdownload"
        else
            MIME_TYPE="application/octet-stream"
        fi
    fi
    
    # Construct upload URL with filename
    # URL encode the filename for safety (if jq is available)
    if command -v jq &> /dev/null; then
        ENCODED_NAME=$(printf '%s' "$ASSET_NAME" | jq -sRr @uri)
    else
        ENCODED_NAME="$ASSET_NAME"
    fi
    FILE_UPLOAD_URL="${BASE_UPLOAD_URL}?name=${ENCODED_NAME}"
    
    UPLOAD_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Authorization: token ${TOKEN}" \
        -H "Content-Type: ${MIME_TYPE}" \
        --data-binary "@${SETUP_FILE}" \
        "${FILE_UPLOAD_URL}" 2>&1)
    
    UPLOAD_HTTP_CODE=$(echo "$UPLOAD_RESPONSE" | tail -n1)
    UPLOAD_BODY=$(echo "$UPLOAD_RESPONSE" | sed '$d')
    
    if [ "$UPLOAD_HTTP_CODE" -eq 201 ]; then
        if command -v jq &> /dev/null; then
            DOWNLOAD_URL=$(echo "$UPLOAD_BODY" | jq -r '.browser_download_url')
        else
            DOWNLOAD_URL=$(echo "$UPLOAD_BODY" | grep -o '"browser_download_url":"[^"]*' | cut -d'"' -f4)
        fi
        echo -e "${GREEN}  ✓ ${ASSET_NAME} uploaded successfully!${NC}"
        if [ -n "$DOWNLOAD_URL" ]; then
            echo -e "${CYAN}    Download: ${DOWNLOAD_URL}${NC}"
        fi
        ((UPLOADED_COUNT++))
    else
        echo -e "${RED}  ✗ ERROR uploading ${ASSET_NAME} (HTTP ${UPLOAD_HTTP_CODE}):${NC}"
        if [ -n "$UPLOAD_BODY" ]; then
            echo "$UPLOAD_BODY" | head -10 | sed 's/^/    /'
        else
            echo -e "    ${YELLOW}No response body. Check your token and network connection.${NC}"
        fi
        ((FAILED_COUNT++))
    fi
    echo ""
done

# Summary
echo -e "${CYAN}========================================${NC}"
if [ $UPLOADED_COUNT -gt 0 ]; then
    echo -e "${GREEN}Successfully uploaded: ${UPLOADED_COUNT} file(s)${NC}"
fi
if [ $FAILED_COUNT -gt 0 ]; then
    echo -e "${RED}Failed to upload: ${FAILED_COUNT} file(s)${NC}"
fi
echo -e "${CYAN}Release URL: ${HTML_URL}${NC}"

# Exit with error if any file failed
if [ $FAILED_COUNT -gt 0 ]; then
    exit 1
fi

