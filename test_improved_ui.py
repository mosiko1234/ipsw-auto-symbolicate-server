#!/usr/bin/env python3
"""
Test script for the improved IPS UI
"""

import requests
import json
import os
from pathlib import Path

def test_api_with_ui():
    """Test the improved API with UI"""
    
    # Configuration
    BASE_URL = "http://localhost:8000"
    
    print("🧪 Testing Improved IPS UI...")
    print(f"Base URL: {BASE_URL}")
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    # Test 2: API Status
    print("\n2. Testing API status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Status: {data.get('status', 'unknown')}")
        else:
            print(f"❌ API Status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API Status error: {e}")
    
    # Test 3: UI Homepage
    print("\n3. Testing UI homepage...")
    try:
        response = requests.get(f"{BASE_URL}/ui", timeout=5)
        if response.status_code == 200:
            print("✅ UI homepage accessible")
            # Check for key elements
            content = response.text
            if "גרור קובץ IPS לכאן" in content:
                print("✅ Updated upload text found")
            if "תהליך הניתוח" in content:
                print("✅ Process steps section found")
            if "טיפים להצלחה" in content:
                print("✅ Success tips section found")
        else:
            print(f"❌ UI homepage failed: {response.status_code}")
    except Exception as e:
        print(f"❌ UI homepage error: {e}")
    
    # Test 4: Check if we have sample IPS files
    print("\n4. Checking for sample IPS files...")
    current_dir = Path(".")
    ips_files = list(current_dir.glob("*.ips"))
    
    if ips_files:
        print(f"✅ Found {len(ips_files)} IPS files:")
        for ips_file in ips_files:
            size_mb = ips_file.stat().st_size / (1024 * 1024)
            print(f"   - {ips_file.name} ({size_mb:.1f} MB)")
        
        # Test 5: Upload test with first IPS file
        if ips_files:
            test_file = ips_files[0]
            print(f"\n5. Testing file upload with {test_file.name}...")
            
            try:
                with open(test_file, 'rb') as f:
                    files = {'file': (test_file.name, f, 'application/octet-stream')}
                    response = requests.post(
                        f"{BASE_URL}/ui/upload", 
                        files=files, 
                        timeout=60
                    )
                
                if response.status_code == 200:
                    content = response.text
                    if "תוצאות Symbolication" in content:
                        print("✅ File upload and processing successful")
                        if "פרטי הקובץ והמכשיר" in content:
                            print("✅ File info section displayed")
                        if "איכות Symbolication" in content:
                            print("✅ Symbolication quality section displayed")
                        if "הורד JSON מלא" in content:
                            print("✅ Download buttons available")
                    else:
                        print("⚠️  Upload succeeded but results page may have issues")
                else:
                    print(f"❌ File upload failed: {response.status_code}")
                    if response.status_code == 422:
                        print("   This might be due to API validation - check file format")
                    
            except Exception as e:
                print(f"❌ File upload error: {e}")
    else:
        print("⚠️  No IPS files found for testing")
        print("   To test file upload, place an .ips file in the current directory")
    
    print("\n🎯 UI Testing Summary:")
    print("- Improved upload interface with drag & drop")
    print("- Better file preview and validation")  
    print("- Enhanced results display with IPS file details")
    print("- Quality indicators and download options")
    print("- Mobile-responsive design")
    
    print("\n📝 To test manually:")
    print(f"1. Open: {BASE_URL}/ui")
    print("2. Upload an IPS file")
    print("3. Check the improved results display")
    print("4. Test JSON and TXT download options")

if __name__ == "__main__":
    test_api_with_ui() 