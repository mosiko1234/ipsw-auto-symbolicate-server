#!/usr/bin/env python3
"""
IPSW Symbol Server CLI
Symbolicate iOS crashlogs using IPSW files
"""

import os
import sys
import argparse
import json
import re
import zipfile
import tempfile
import shutil
import subprocess
from pathlib import Path

def parse_crashlog(crashlog_path):
    """Parse iOS crashlog to extract basic information"""
    with open(crashlog_path, 'r') as f:
        content = f.read()
    
    info = {
        'process': None,
        'device': None,
        'os_version': None,
        'build_id': None,
        'architecture': 'arm64e',
        'crashed_thread': None,
        'stack_trace': [],
        'is_kernel_panic': False,
        'file_format': 'unknown'
    }
    
    # Check if this is a JSON stackshot file
    if content.strip().startswith('{'):
        return parse_json_stackshot(content, info)
    
    # Otherwise parse as traditional iOS crash report
    return parse_traditional_crashlog(content, info)

def parse_json_stackshot(content, info):
    """Parse JSON stackshot format"""
    try:
        lines = content.strip().split('\n')
        
        # Parse header JSON (first line)
        header_json = None
        try:
            header_json = json.loads(lines[0])
        except:
            pass
        
        # Parse main JSON (lines 1 to end, multi-line)
        main_json_text = '\n'.join(lines[1:])
        main_json = json.loads(main_json_text)
        
        if main_json:
            info['file_format'] = 'json_stackshot'
            info['device'] = main_json.get('product', None)
            info['os_version'] = main_json.get('build', None)
            info['is_kernel_panic'] = 'panic' in main_json.get('reason', '').lower()
            
            # Get process info
            target_pid = str(main_json.get('pid', ''))
            if 'processByPid' in main_json and target_pid in main_json['processByPid']:
                proc_data = main_json['processByPid'][target_pid]
                process_name = proc_data.get('procname', 'unknown')
                info['process'] = f"{process_name} [PID {target_pid}]"
            elif target_pid:
                info['process'] = f"Process PID {target_pid}"
            
            # Extract reason info
            reason = main_json.get('reason', '')
            if reason:
                info['crash_reason'] = reason
            
            # Extract stack traces from target process
            if 'processByPid' in main_json and target_pid in main_json['processByPid']:
                proc_data = main_json['processByPid'][target_pid]
                stack_count = 0
                
                if 'threadById' in proc_data:
                    threads = proc_data['threadById']
                    
                    # Process threads in order, prioritizing main/first threads
                    thread_list = list(threads.items())
                    for thread_id, thread_data in thread_list:
                        if isinstance(thread_data, dict):
                            # Check for user frames first (more relevant for symbolication)
                            if 'userFrames' in thread_data:
                                frames = thread_data['userFrames']
                                for i, frame in enumerate(frames):
                                    if isinstance(frame, dict):
                                        # Extract binary name and symbol
                                        binary_name = frame.get('binary', 'unknown')
                                        symbol_name = frame.get('symbol', '')
                                        image_offset = frame.get('imageOffset', 0)
                                        
                                        info['stack_trace'].append({
                                            'frame_number': str(stack_count),
                                            'library': binary_name,
                                            'address': f"0x{image_offset:x}" if image_offset else "0x0",
                                            'symbol': symbol_name or f"frame_{i}",
                                            'thread_id': thread_id,
                                            'pid': target_pid
                                        })
                                        stack_count += 1
                            
                            # Also check for kernel frames
                            if 'kernelFrames' in thread_data:
                                frames = thread_data['kernelFrames']
                                for i, frame in enumerate(frames):
                                    if isinstance(frame, list) and len(frame) >= 2:
                                        addr = frame[1] if isinstance(frame[1], int) else 0
                                        info['stack_trace'].append({
                                            'frame_number': str(stack_count),
                                            'library': 'kernel',
                                            'address': f"0x{addr:x}" if addr else "0x0",
                                            'symbol': f"kernel_frame_{i}",
                                            'thread_id': thread_id,
                                            'pid': target_pid
                                        })
                                        stack_count += 1
                            
                            # Set crashed thread (usually the first thread or one with high priority)
                            if not info['crashed_thread']:
                                info['crashed_thread'] = int(thread_id)
            
            return info
        
    except (json.JSONDecodeError, Exception) as e:
        print(f"⚠️  Failed to parse JSON stackshot: {e}")
        info['file_format'] = 'json_error'
        return info
    
    return info

def parse_traditional_crashlog(content, info):
    """Parse traditional iOS crash report format"""
    info['file_format'] = 'traditional_ios'
    
    lines = content.split('\n')
    in_thread_section = False
    in_kernel_section = False
    
    # Check if this is a kernel panic
    if any('panic' in line.lower() for line in lines[:10]):
        info['is_kernel_panic'] = True
    
    for line in lines:
        line = line.strip()
        
        # Extract basic info
        if line.startswith('Process:'):
            info['process'] = line.split(':', 1)[1].strip()
        elif line.startswith('Hardware Model:'):
            info['device'] = line.split(':', 1)[1].strip()
        elif line.startswith('OS Version:'):
            info['os_version'] = line.split(':', 1)[1].strip()
        elif line.startswith('BuildID:'):
            info['build_id'] = line.split(':', 1)[1].strip()
        elif 'Crashed:' in line and 'Thread' in line:
            match = re.search(r'Thread (\d+)', line)
            if match:
                info['crashed_thread'] = int(match.group(1))
                in_thread_section = True
        elif 'Backtrace' in line and 'CPU' in line:
            # Start of kernel backtrace section
            in_kernel_section = True
        elif in_kernel_section and line.startswith('0x') and ':' in line:
            # Parse kernel backtrace frame
            parts = line.split(' : ')
            if len(parts) == 2:
                frame_addr = parts[0].strip()
                return_info = parts[1].strip()
                
                return_parts = return_info.split(' ', 1)
                return_addr = return_parts[0] if return_parts else None
                symbol_info = return_parts[1] if len(return_parts) > 1 else None
                
                if return_addr and return_addr.startswith('0x'):
                    frame_info = {
                        'frame_number': str(len(info['stack_trace'])),
                        'library': 'kernel',
                        'address': return_addr,
                        'symbol': symbol_info,
                        'frame_address': frame_addr
                    }
                    info['stack_trace'].append(frame_info)
        elif in_thread_section and re.match(r'^\s*\d+\s+', line):
            # Parse userspace stack frame: "0   libsystem_c.dylib         0x00000001a734e000 malloc + 32"
            parts = line.split()
            if len(parts) >= 3:
                frame_number = parts[0]
                library = parts[1]
                address = None
                symbol = None
                
                # Find the address (starts with 0x)
                for i, part in enumerate(parts[2:], 2):
                    if part.startswith('0x'):
                        address = part
                        symbol = ' '.join(parts[i+1:]) if i+1 < len(parts) else None
                        break
                
                if address:
                    frame_info = {
                        'frame_number': frame_number,
                        'library': library,
                        'address': address,
                        'symbol': symbol
                    }
                    info['stack_trace'].append(frame_info)
        elif in_thread_section and line == '':
            in_thread_section = False
    
    return info

def extract_dyld_cache_with_ipsw_cli(ipsw_path, output_dir, ipsw_cli_path):
    """Extract dyld_shared_cache from IPSW using ipsw CLI"""
    print(f"📦 Extracting dyld_shared_cache from {os.path.basename(ipsw_path)} using ipsw CLI...")
    
    try:
        # Use ipsw extract --dyld command
        cmd = [ipsw_cli_path, 'extract', '--dyld', '--output', output_dir, ipsw_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 minutes timeout
        
        if result.returncode == 0:
            print("  ✅ Extraction completed successfully!")
            
            # Debug: List all files in output directory
            print(f"  🔍 Checking output directory: {output_dir}")
            try:
                all_files = []
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, output_dir)
                        all_files.append(rel_path)
                        print(f"     Found file: {rel_path}")
                
                # Find extracted cache files
                cache_files = []
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        if 'dyld_shared_cache' in file:
                            cache_path = os.path.join(root, file)
                            cache_files.append(cache_path)
                            print(f"  📄 Cache file: {os.path.relpath(cache_path, output_dir)}")
                
                if cache_files:
                    return cache_files
                else:
                    print(f"❌ No dyld_shared_cache files found. Total files extracted: {len(all_files)}")
                    return None
            except Exception as e:
                print(f"❌ Error scanning output directory: {e}")
                return None
        else:
            print(f"❌ Extraction failed:")
            print(f"   Command: {' '.join(cmd)}")
            print(f"   Error: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("❌ Extraction timed out (>10 minutes)")
        return None
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        return None

def symbolicate_with_ipsw_cli(ips_path, ipsw_path_file):
    """Symbolicate IPS file using IPSW symbols via ipsw CLI"""
    print(f"🔍 Symbolicating {os.path.basename(ips_path)} with {os.path.basename(ipsw_path_file)}...")
    
    # Check if ipsw CLI is available
    ipsw_path = None
    
    # Try common paths
    possible_paths = [
        'ipsw',  # In PATH
        '/opt/homebrew/bin/ipsw',  # Homebrew on Apple Silicon
        '/usr/local/bin/ipsw',     # Homebrew on Intel
        os.path.expanduser('~/bin/ipsw'),  # User bin
    ]
    
    for path in possible_paths:
        try:
            result = subprocess.run([path, 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                ipsw_path = path
                print(f"  📱 Using ipsw CLI: {result.stdout.strip()}")
                print(f"     Found at: {path}")
                break
        except (FileNotFoundError, OSError):
            continue
    
    if not ipsw_path:
        print("❌ ipsw CLI not found. Please install it:")
        print("   brew install blacktop/tap/ipsw")
        print("   or download from: https://github.com/blacktop/ipsw")
        print("\n🔍 Searched in these locations:")
        for path in possible_paths:
            print(f"   - {path}")
        return None
    
    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract dyld_shared_cache from IPSW using ipsw CLI
        cache_files = extract_dyld_cache_with_ipsw_cli(ipsw_path_file, temp_dir, ipsw_path)
        if not cache_files:
            return None
        
        # Use the main dyld_shared_cache file (the one without extension)
        main_cache = next((f for f in cache_files if f.endswith('dyld_shared_cache_arm64e') and not '.' in os.path.basename(f).split('_')[-1]), cache_files[0])
        
        print(f"🔧 Running symbolication using: {os.path.basename(main_cache)}")
        
        # Run ipsw symbolicate command
        # First try with IPSW file (better for JSON stackshots)
        try:
            cmd = [ipsw_path, 'symbolicate', ips_path, ipsw_path_file]
            print(f"  🔧 Command: {' '.join([ipsw_path, 'symbolicate', os.path.basename(ips_path), os.path.basename(ipsw_path_file)])}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ Symbolication completed successfully!")
                return result.stdout
            else:
                print(f"❌ Symbolication failed:")
                print(f"   Error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ Symbolication timed out (>5 minutes)")
            return None
        except Exception as e:
            print(f"❌ Error running symbolication: {e}")
            return None

def create_pretty_output_from_parsed_data(crash_info):
    """Create a pretty-printed output from parsed crash data"""
    output = []
    
    output.append("=" * 60)
    output.append("📱 SYMBOLICATED STACKSHOT REPORT")
    output.append("=" * 60)
    output.append("")
    
    # Basic info
    output.append(f"📋 Crash Information:")
    output.append(f"   Process: {crash_info.get('process', 'Unknown')}")
    output.append(f"   Device: {crash_info.get('device', 'Unknown')}")
    output.append(f"   OS Version: {crash_info.get('os_version', 'Unknown')}")
    output.append(f"   File Format: {crash_info.get('file_format', 'Unknown')}")
    
    if crash_info.get('crash_reason'):
        output.append(f"   Crash Reason: {crash_info['crash_reason'][:100]}...")
    
    output.append("")
    
    # Stack trace
    stack_frames = crash_info.get('stack_trace', [])
    if stack_frames:
        output.append(f"🔍 Stack Trace ({len(stack_frames)} frames):")
        output.append("")
        
        current_thread = None
        for frame in stack_frames:
            thread_id = frame.get('thread_id', 'unknown')
            
            # Show thread header
            if thread_id != current_thread:
                current_thread = thread_id
                output.append(f"Thread {thread_id}:")
            
            # Format frame
            frame_num = frame.get('frame_number', '?')
            library = frame.get('library', 'unknown')
            address = frame.get('address', '0x0')
            symbol = frame.get('symbol', '<unknown>')
            
            # Clean up symbol name
            if symbol and symbol != '<unknown>':
                clean_symbol = symbol
            else:
                clean_symbol = f"<unknown_{frame_num}>"
            
            output.append(f"  {frame_num:>2}: {library:<30} {address:<18} {clean_symbol}")
        
    else:
        output.append("❌ No stack frames found")
    
    output.append("")
    output.append("💡 Note: This is a parsed JSON stackshot. For full symbolication,")
    output.append("   user frames would need matching symbol data.")
    output.append("")
    
    return "\n".join(output)

def main():
    parser = argparse.ArgumentParser(
        description='Symbolicate iOS crashlogs using IPSW files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s crash.ips firmware.ipsw
  %(prog)s --json crash.ips firmware.ipsw > result.json
  %(prog)s --info crash.ips
        '''
    )
    
    parser.add_argument('ips_file', help='iOS crashlog file (.ips)')
    parser.add_argument('ipsw_file', nargs='?', help='IPSW firmware file (.ipsw)')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--info', action='store_true', help='Show crashlog info only (no symbolication)')
    parser.add_argument('--output', '-o', help='Output file for symbolicated result')
    
    args = parser.parse_args()
    
    # Validate input files
    if not os.path.exists(args.ips_file):
        print(f"❌ IPS file not found: {args.ips_file}")
        sys.exit(1)
    
    if not args.info and not args.ipsw_file:
        print("❌ IPSW file required for symbolication")
        parser.print_help()
        sys.exit(1)
    
    if args.ipsw_file and not os.path.exists(args.ipsw_file):
        print(f"❌ IPSW file not found: {args.ipsw_file}")
        sys.exit(1)
    
    # Parse crashlog
    print(f"📋 Parsing crashlog: {os.path.basename(args.ips_file)}")
    crash_info = parse_crashlog(args.ips_file)
    
    if args.info:
        # Show crashlog info only
        if args.json:
            print(json.dumps(crash_info, indent=2))
        else:
            print(f"\n📱 Crash Information:")
            print(f"   Process: {crash_info['process']}")
            print(f"   Device: {crash_info['device']}")
            print(f"   OS Version: {crash_info['os_version']}")
            print(f"   Build ID: {crash_info['build_id']}")
            print(f"   Crashed Thread: {crash_info['crashed_thread']}")
            print(f"   Stack Frames: {len(crash_info['stack_trace'])}")
            print(f"   Kernel Panic: {crash_info['is_kernel_panic']}")
        return
    
    # Perform symbolication
    symbolicated_output = symbolicate_with_ipsw_cli(args.ips_file, args.ipsw_file)
    
    if symbolicated_output:
        if args.output:
            # Save to file
            with open(args.output, 'w') as f:
                f.write(symbolicated_output)
            print(f"💾 Symbolicated output saved to: {args.output}")
        else:
            # Print to stdout
            print("\n" + "="*60)
            print("📋 SYMBOLICATED CRASHLOG")
            print("="*60)
            print(symbolicated_output)
    else:
        print("❌ Symbolication failed")
        sys.exit(1)

if __name__ == '__main__':
    main() 