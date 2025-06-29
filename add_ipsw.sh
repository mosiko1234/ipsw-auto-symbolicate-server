#!/bin/bash
# Script for adding new IPSW files to the symbol system
# IPSW Symbol Server - Add IPSW Helper Script

set -e

IPSW_FILE="$1"
IPSW_DIR="./ipsw_files"
BASE_URL="http://localhost:3993"

function usage() {
    echo "Usage: $0 <ipsw_file_path>"
    echo "Example: $0 ~/Downloads/iPhone15,2_17.5_21F79_Restore.ipsw"
    echo ""
    echo "The script will:"
    echo "1. Copy the file to ipsw_files directory"
    echo "2. Verify file detection in IPSW list"
    echo "3. Scan the file in the system"
    echo "4. Display scan status"
}

function check_server() {
    echo "🔍 Checking if server is running..."
    if ! curl -s "${BASE_URL}/v1/_ping" > /dev/null; then
        echo "❌ Server is not available. Run: docker-compose up -d"
        exit 1
    fi
    echo "✅ Server is running"
}

function copy_file() {
    local file="$1"
    local filename=$(basename "$file")
    
    echo "📁 Copying file: $filename"
    cp "$file" "$IPSW_DIR/"
    echo "✅ File copied to: ${IPSW_DIR}/${filename}"
}

function verify_file_detected() {
    local filename="$1"
    
    echo "🔍 Checking file detection in IPSW list..."
    local detected=$(curl -s "${BASE_URL}/v1/ipsw/list" | jq -r ".ipsw_files[] | select(.filename==\"${filename}\") | .filename")
    
    if [ "$detected" = "$filename" ]; then
        echo "✅ File detected in list"
        
        # Show file details
        echo "📱 File details:"
        curl -s "${BASE_URL}/v1/ipsw/list" | jq ".ipsw_files[] | select(.filename==\"${filename}\")"
    else
        echo "⚠️ File not detected in list"
        exit 1
    fi
}

function scan_ipsw() {
    local filename="$1"
    local ipsw_path="/app/ipsw_files/${filename}"
    
    echo "🔄 Scanning IPSW file..."
    local scan_result=$(curl -s -X POST "${BASE_URL}/v1/syms/scan" \
        -H "Content-Type: application/json" \
        -d "{\"path\": \"${ipsw_path}\"}")
    
    echo "📊 Scan result:"
    echo "$scan_result" | jq '.'
    
    local status=$(echo "$scan_result" | jq -r '.status // "unknown"')
    if [ "$status" = "completed" ]; then
        echo "✅ Scan completed successfully!"
    else
        echo "⚠️ Scan issue - check result above"
    fi
}

function show_summary() {
    echo ""
    echo "🎉 Summary:"
    echo "📋 List all IPSW: curl ${BASE_URL}/v1/ipsw/list"
    echo "📋 List scans: curl ${BASE_URL}/v1/syms/scans"
    echo "🔧 Symbolicate: curl -F \"crashlog=@file.ips\" ${BASE_URL}/v1/symbolicate"
    echo ""
    echo "System ready for use! 🚀"
}

# Main execution
if [ $# -eq 0 ]; then
    usage
    exit 1
fi

if [ ! -f "$IPSW_FILE" ]; then
    echo "❌ File not found: $IPSW_FILE"
    exit 1
fi

if [ ! -d "$IPSW_DIR" ]; then
    echo "📁 Creating ipsw_files directory..."
    mkdir -p "$IPSW_DIR"
fi

filename=$(basename "$IPSW_FILE")

echo "🚀 Starting IPSW file addition: $filename"
echo "========================================"

check_server
copy_file "$IPSW_FILE"
sleep 2  # Give server time to detect the file
verify_file_detected "$filename"
scan_ipsw "$filename"
show_summary 