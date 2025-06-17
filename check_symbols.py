#!/usr/bin/env python3
import json

with open('full_response.json', 'r') as f:
    data = json.load(f)
    
print('Success:', data.get('success'))
print('Symbols count:', len(data.get('symbols', {})))
print('Message:', data.get('message'))
print('Symbolication time:', data.get('symbolication_time'))

symbols = data.get('symbols', {})
if symbols:
    print('\nFirst 10 symbols:')
    for i, (addr, symbol) in enumerate(list(symbols.items())[:10]):
        print(f'  {addr}: {symbol}')
else:
    print('\nNo symbols found!')
    print('Keys in response:', list(data.keys())) 