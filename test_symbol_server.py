#!/usr/bin/env python3
import requests
import json

# Test the Symbol Server directly
url = "http://localhost:3993/v1/symbolicate"

# Read the crash log
with open('stacks-2025-06-16-134742.ips', 'r') as f:
    crash_content = f.read()

# Prepare the request data
data = {
    "crash_content": crash_content,
    "ios_version": "18.5", 
    "device_model": "iPhone15,2"
}

print("🔍 Testing Symbol Server directly...")
print(f"URL: {url}")
print(f"Device: {data['device_model']}")
print(f"iOS: {data['ios_version']}")
print(f"Crash content length: {len(crash_content)} characters")

try:
    response = requests.post(url, json=data)
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message')}")
        
        symbols = result.get('symbols', {})
        symbolicated_crash = result.get('symbolicated_crash', '')
        
        print(f"Symbols count: {len(symbols) if symbols else 0}")
        print(f"Symbolicated crash length: {len(symbolicated_crash) if symbolicated_crash else 0}")
        
        if symbols:
            print("\nFirst 5 symbols:")
            for i, (addr, symbol) in enumerate(list(symbols.items())[:5]):
                print(f"  {addr}: {symbol}")
        
        if symbolicated_crash and len(symbolicated_crash) != len(crash_content):
            print(f"\n✅ Crash log was modified (original: {len(crash_content)}, symbolicated: {len(symbolicated_crash)})")
        elif symbolicated_crash:
            print(f"\n⚠️ Crash log was not modified (same length)")
        else:
            print(f"\n❌ No symbolicated crash returned")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}") 