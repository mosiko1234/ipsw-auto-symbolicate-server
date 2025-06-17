#!/usr/bin/env python3
"""
Format symbolication results for better readability
Usage: python format_results.py < response.json
Or: curl -X POST ... | python format_results.py
"""

import json
import sys
from datetime import datetime

def extract_kernel_addresses(crash_data):
    """Extract kernel addresses from crash log data"""
    import re
    
    addresses = []
    
    # Look for kernelFrames sections in the crash log
    kernel_frames_pattern = r'"kernelFrames"\s*:\s*\[(.*?)\]'
    matches = re.findall(kernel_frames_pattern, crash_data, re.DOTALL)
    
    for match in matches:
        # Extract long numbers (10+ digits) which are likely kernel addresses
        address_pattern = r'(\d{10,})'
        addr_matches = re.findall(address_pattern, match)
        
        for addr_str in addr_matches:
            try:
                addr = int(addr_str)
                # Convert to virtual address by ORing with kernel base
                virtual_addr = addr | 0xfffffff000000000
                addresses.append(virtual_addr)
            except ValueError:
                continue
    
    return list(set(addresses))  # Remove duplicates

def format_symbolication_response(data):
    """Format the symbolication API response in a developer-friendly way"""
    
    print("=" * 80)
    print("🔍 iOS KERNEL SYMBOLICATION RESULTS")
    print("=" * 80)
    print()
    
    # Success status
    success = data.get('success', False)
    status_emoji = "✅" if success else "❌"
    print(f"{status_emoji} Status: {'SUCCESS' if success else 'FAILED'}")
    
    # Timing information
    if 'total_time' in data:
        print(f"⏱️  Total Processing Time: {data['total_time']:.3f} seconds")
    if 'symbolication_time' in data:
        print(f"🔧 Symbolication Time: {data['symbolication_time']:.3f} seconds")
    if 'download_time' in data and data['download_time']:
        print(f"📥 Download Time: {data['download_time']:.3f} seconds")
    
    print(f"🕒 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Device information from crash log
    crash_data = data.get('symbolicated_output', '')
    if crash_data:
        print("📱 CRASH LOG ANALYSIS")
        print("-" * 40)
        
        # Extract kernel addresses from crash log
        kernel_addresses = extract_kernel_addresses(crash_data)
        
        if kernel_addresses:
            print(f"🎯 Found {len(kernel_addresses)} kernel addresses:")
            for i, addr in enumerate(kernel_addresses[:10], 1):  # Show first 10
                print(f"  {i:2d}. 0x{addr:016x}")
            
            if len(kernel_addresses) > 10:
                print(f"     ... and {len(kernel_addresses) - 10} more addresses")
        else:
            print("❓ No kernel addresses found in crash log")
        
        # Look for device info in crash log
        if '"os_version"' in crash_data:
            import re
            os_match = re.search(r'"os_version"\s*:\s*"([^"]+)"', crash_data)
            if os_match:
                print(f"📱 OS Version: {os_match.group(1)}")
        
        print()
    
    # S3 information
    if 's3_info' in data and data['s3_info']:
        s3_info = data['s3_info']
        print("☁️  S3 STORAGE INFORMATION")
        print("-" * 40)
        for key, value in s3_info.items():
            print(f"{key}: {value}")
        print()
    
    # Error information
    if not success and 'error' in data:
        print("❌ ERROR DETAILS")
        print("-" * 40)
        print(f"Error: {data['error']}")
        print()
    
    # Message from server
    if 'message' in data:
        print("💬 SERVER MESSAGE")
        print("-" * 40)
        print(data['message'])
        print()
    
    # Raw symbolicated output info
    if crash_data:
        print("📄 SYMBOLICATED OUTPUT")
        print("-" * 40)
        print(f"Output Size: {len(crash_data):,} characters")
        
        # Count lines that might contain symbols
        lines = crash_data.split('\n')
        symbol_lines = []
        unknown_lines = []
        
        for line in lines:
            if '<unknown>' in line and '+0x' in line:
                unknown_lines.append(line.strip())
            elif '+' in line and '0x' in line and '<unknown>' not in line and any(func in line for func in ['_', 'kernel', 'IOKit', 'com.apple']):
                symbol_lines.append(line.strip())
        
        print(f"✅ Lines with Real Symbols: {len(symbol_lines)}")
        print(f"❌ Lines with Unknown Symbols: {len(unknown_lines)}")
        
        if symbol_lines:
            print(f"\n🎯 Sample Symbolicated Lines:")
            for i, symbol in enumerate(symbol_lines[:5]):
                # Truncate very long lines
                display_line = symbol[:100] + "..." if len(symbol) > 100 else symbol
                print(f"   {i+1}. {display_line}")
        
        print()
    
    # Summary and recommendations
    print("📋 SUMMARY")
    print("-" * 40)
    
    if success:
        if crash_data:
            kernel_addresses = extract_kernel_addresses(crash_data)
            lines = crash_data.split('\n')
            symbol_lines = [l for l in lines if '+' in l and '0x' in l and '<unknown>' not in l and any(func in l for func in ['_', 'kernel', 'IOKit', 'com.apple'])]
            
            if symbol_lines:
                print("🎉 Kernel symbolication is working!")
                print(f"   - Found {len(kernel_addresses)} kernel addresses")
                print(f"   - Successfully symbolicated {len(symbol_lines)} code locations")
                print("💡 Your iOS crash analysis is ready for debugging")
            elif kernel_addresses:
                print("⚠️  Partial success:")
                print(f"   - Found {len(kernel_addresses)} kernel addresses")
                print("   - But no symbols were resolved")
                print("💡 Check if the correct IPSW/signatures are loaded")
            else:
                print("❌ No kernel addresses found in crash log")
                print("💡 Verify the crash log format and content")
        else:
            print("❌ No symbolicated output received")
    else:
        print("❌ Symbolication failed")
        print("💡 Check the error details above")
    
    print()
    print("=" * 80)

def main():
    try:
        # Read JSON from stdin
        input_data = sys.stdin.read().strip()
        
        if not input_data:
            print("Error: No input data provided", file=sys.stderr)
            print("Usage: curl -X POST ... | python format_results.py", file=sys.stderr)
            sys.exit(1)
        
        # Parse JSON
        data = json.loads(input_data)
        
        # Format and display
        format_symbolication_response(data)
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input - {e}", file=sys.stderr)
        print("First 200 characters of input:", file=sys.stderr)
        print(input_data[:200], file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 