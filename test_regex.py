#!/usr/bin/env python3
import re

with open('stacks-2025-06-16-134742.ips', 'r') as f:
    content = f.read()

pattern = r'"kernelFrames"\s*:\s*\[(.*?)\]'
matches = re.findall(pattern, content, re.DOTALL)
print(f'Found {len(matches)} kernelFrames sections')

if matches:
    first_match = matches[0]
    print(f'First match length: {len(first_match)} chars')
    print(f'First match sample (first 300 chars):\n{first_match[:300]}')
    
    # Updated regex to handle multiline format
    frame_pattern = r'\[\s*(\d+)\s*,\s*(\d+)\s*\]'
    frame_matches = re.findall(frame_pattern, first_match, re.DOTALL)
    print(f'\nFound {len(frame_matches)} frames in first section')
    
    if frame_matches:
        for i, (offset, addr) in enumerate(frame_matches[:5]):
            addr_int = int(addr)
            print(f'Frame {i}: offset={offset}, addr={addr} (0x{addr_int:x})')
            
            # Check if it's a kernel address
            if addr_int > 0x1000000000:  # 64GB threshold
                print(f'  -> This is a kernel address!')
            else:
                print(f'  -> This is NOT a kernel address (too small)')
    else:
        print('No frames found with current regex')
        
        # Try a simpler approach - look for numbers directly
        simple_pattern = r'(\d{10,})'  # Look for long numbers (10+ digits)
        simple_matches = re.findall(simple_pattern, first_match)
        print(f'Found {len(simple_matches)} long numbers: {simple_matches[:5]}')
else:
    print('No kernelFrames found!') 