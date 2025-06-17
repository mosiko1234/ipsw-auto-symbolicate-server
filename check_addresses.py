#!/usr/bin/env python3

print('Kernel address from crash log:')
addr = 86032730544
print(f'Decimal: {addr}')
print(f'Hex: 0x{addr:x}')
print()

print('Kernel addresses from symbols:')
print('0xfffffff007ec82ac')
print('0xfffffff007ec8a2c') 
print('0xfffffff007ec8dd4')
print()

print('Crash addresses seen in logs:')
print('0x1407f349b0')
print('0x1407f38404')
print('0x1407ed0398')
print()

print('Converting crash addresses to match symbols range:')
crash_addrs = [0x1407f349b0, 0x1407f38404, 0x1407ed0398]
for addr in crash_addrs:
    # Try different offsets to match kernel space
    kernel_addr = addr + 0xfffffff000000000
    print(f'0x{addr:x} + kernel_base = 0x{kernel_addr:x}') 