#!/bin/bash
# Script for symbolication of crashlog files
# IPSW Symbol Server - Symbolication Helper Script

set -e

CRASHLOG_FILE="$1"
OUTPUT_FILE="$2"
BASE_URL="http://localhost:3993"

function usage() {
    echo "Usage: $0 <crashlog_file> [output_file]"
    echo "Example: $0 crash.ips symbolicated_crash.txt"
    echo "Example: $0 MyApp-crash.ips  # will create file with _symbolicated.txt suffix"
    echo ""
    echo "The script will:"
    echo "1. Check if server is running"
    echo "2. Send crashlog for symbolication"
    echo "3. Save result to file"
    echo "4. Display summary"
}

function check_server() {
    echo "🔍 Checking if server is running..."
    if ! curl -s "${BASE_URL}/v1/_ping" > /dev/null; then
        echo "❌ Server is not available. Run: docker-compose up -d"
        exit 1
    fi
    echo "✅ Server is running"
}

function check_ipsw_available() {
    echo "🔍 Checking available IPSW files..."
    local count=$(curl -s "${BASE_URL}/v1/ipsw/list" | jq '.total')
    
    if [ "$count" -eq 0 ]; then
        echo "⚠️ No IPSW files available in system"
        echo "💡 Add IPSW file with: ./add_ipsw.sh <ipsw_file>"
        exit 1
    fi
    
    echo "✅ Found $count IPSW files in system"
    
    # Show available IPSW list
    echo "📱 Available IPSW files:"
    curl -s "${BASE_URL}/v1/ipsw/list" | jq -r '.ipsw_files[] | "  - \(.device_model) iOS \(.os_version) (\(.build_id))"'
}

function symbolicate_crash() {
    local crashlog="$1"
    local output="$2"
    
    echo "🔄 Performing symbolication..."
    
    # Send crashlog file
    local result=$(curl -s -F "crashlog=@${crashlog}" "${BASE_URL}/v1/symbolicate")
    
    # Check if symbolication succeeded
    local success=$(echo "$result" | jq -r '.symbolicated // false')
    
    if [ "$success" = "true" ]; then
        echo "✅ Symbolication succeeded!"
        
        # Save the result
        echo "$result" | jq -r '.output' > "$output"
        echo "💾 Result saved to: $output"
        
        # Show details about the IPSW used
        local used_ipsw=$(echo "$result" | jq -r '.used_ipsw // "unknown"')
        local method=$(echo "$result" | jq -r '.method // "unknown"')
        
        echo "📊 Symbolication details:"
        echo "  🔧 Method: $method"
        echo "  📱 IPSW: $used_ipsw"
        echo "  ⏰ Time: $(echo "$result" | jq -r '.timestamp // "unknown"')"
        
    else
        echo "❌ Symbolication failed!"
        echo "Error: $(echo "$result" | jq -r '.error // "unknown"')"
        exit 1
    fi
}

function show_file_preview() {
    local file="$1"
    
    echo ""
    echo "👁️ Result preview:"
    echo "=====================================";
    head -n 20 "$file"
    echo ""
    echo "... (see full file at: $file)"
}

function show_summary() {
    local input="$1"
    local output="$2"
    
    echo ""
    echo "🎉 Symbolication completed successfully!"
    echo "=================================="
    echo "📥 Input file: $input"
    echo "📤 Output file: $output"
    echo "📊 Result size: $(wc -l < "$output") lines"
    echo ""
    echo "💡 Tips:"
    echo "  - Open in editor: open '$output'"
    echo "  - Search: grep 'function_name' '$output'"
    echo "  - Delete: rm '$output'"
}

# Main execution
if [ $# -eq 0 ]; then
    usage
    exit 1
fi

if [ ! -f "$CRASHLOG_FILE" ]; then
    echo "❌ Crashlog file not found: $CRASHLOG_FILE"
    exit 1
fi

# Set automatic output filename if not provided
if [ -z "$OUTPUT_FILE" ]; then
    base_name=$(basename "$CRASHLOG_FILE" .ips)
    OUTPUT_FILE="${base_name}_symbolicated.txt"
fi

echo "🚀 Starting symbolication of: $(basename "$CRASHLOG_FILE")"
echo "========================================"

check_server
check_ipsw_available
symbolicate_crash "$CRASHLOG_FILE" "$OUTPUT_FILE"
show_file_preview "$OUTPUT_FILE"
show_summary "$CRASHLOG_FILE" "$OUTPUT_FILE" 