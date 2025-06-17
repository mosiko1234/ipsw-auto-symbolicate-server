#!/usr/bin/env python3
import json

with open('full_response.json', 'r') as f:
    data = json.load(f)
    
print('Success:', data.get('success'))
print('Message:', data.get('message'))
print('Symbolication time:', data.get('symbolication_time'))
print('Keys in response:', list(data.keys()))

symbolicated_output = data.get('symbolicated_output', '')
if symbolicated_output:
    print(f'\nSymbolicated output length: {len(symbolicated_output)} characters')
    print('First 1000 characters:')
    print(symbolicated_output[:1000])
    print('\n... (truncated)')
    
    # Count how many symbols are in the output
    lines = symbolicated_output.split('\n')
    symbol_lines = [line for line in lines if ' + ' in line and '0x' in line]
    print(f'\nEstimated symbols found: {len(symbol_lines)}')
    
    if symbol_lines:
        print('Sample symbolicated lines:')
        for i, line in enumerate(symbol_lines[:5]):
            print(f'  {line}')
else:
    print('\nNo symbolicated output found!') 