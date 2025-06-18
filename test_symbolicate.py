#!/usr/bin/env python3
import json
import requests

def test_symbolication():
    # Read the crash file
    with open('stacks-2025-06-16-134742.ips', 'r') as f:
        crash_content = f.read()

    # Test the file upload endpoint (which uses files instead of JSON)
    print(f"Testing file upload with {len(crash_content)} chars of crash content...")
    
    # Create a file-like object for the upload
    files = {
        'file': ('stacks-2025-06-16-134742.ips', crash_content, 'application/json')
    }
    
    response = requests.post('http://localhost:8000/symbolicate', files=files)
    print('Status:', response.status_code)
    
    if response.status_code == 200:
        result = response.json()
        print('Success:', result.get('success'))
        print('Message:', result.get('message'))
        print('Analysis ID:', result.get('analysis_id'))
        if result.get('file_info'):
            file_info = result['file_info']
            print(f"Device: {file_info.get('device_model')}")
            print(f"iOS: {file_info.get('ios_version')}")
            print(f"Build: {file_info.get('build_version')}")
            print(f"Bug Type: {file_info.get('bug_type')}")
        print('Findings:')
        for finding in result.get('findings', []):
            print(f"  {finding}")
    else:
        print('Error response:', response.text)

if __name__ == '__main__':
    test_symbolication() 