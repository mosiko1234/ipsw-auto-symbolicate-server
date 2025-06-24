#!/usr/bin/env python3
"""
IPSW Symbol Server CLI Tool - Unified Local & Network Client
Beautiful terminal interface for symbolication requests
"""

import argparse
import requests
import json
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
import time

# Rich library for beautiful terminal output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    from rich.text import Text
    from rich.align import Align
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  For the best experience, install rich: pip install rich")

# Colorama for cross-platform colored output (fallback)
try:
    from colorama import init, Fore, Back, Style
    init()
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

class IPSWCLIFormatter:
    """Beautiful terminal formatter for IPSW symbolication results"""
    
    def __init__(self, mode="local"):
        self.console = Console() if RICH_AVAILABLE else None
        self.mode = mode  # "local" or "network"
        
    def print_banner(self):
        """Print a beautiful banner"""
        if RICH_AVAILABLE:
            if self.mode == "network":
                banner = """
╔═══════════════════════════════════════════════════════════════╗
║              🌐 IPSW Symbol Server CLI - Network              ║
║              Professional iOS Crash Symbolication            ║
║                     Remote Server Client                     ║
╚═══════════════════════════════════════════════════════════════╝
"""
            else:
                banner = """
╔═══════════════════════════════════════════════════════════════╗
║                  🚀 IPSW Symbol Server CLI                   ║
║              Professional iOS Crash Symbolication            ║
╚═══════════════════════════════════════════════════════════════╝
"""
            self.console.print(Panel(
                Align.center(banner.strip()),
                style="bold blue",
                box=box.DOUBLE
            ))
        else:
            self._print_fallback_banner()
    
    def _print_fallback_banner(self):
        """Fallback banner without rich"""
        if COLORAMA_AVAILABLE:
            print(f"{Fore.CYAN}{Style.BRIGHT}")
        print("=" * 65)
        if self.mode == "network":
            print("🌐 IPSW Symbol Server CLI - Network Client")
        else:
            print("🚀 IPSW Symbol Server CLI - Professional iOS Crash Symbolication")
        print("=" * 65)
        if COLORAMA_AVAILABLE:
            print(f"{Style.RESET_ALL}")
    
    def print_connection_info(self, server_url, is_local=True):
        """Print connection information"""
        if RICH_AVAILABLE:
            table = Table(title="🔗 Connection Information", box=box.ROUNDED)
            table.add_column("Property", style="bold cyan")
            table.add_column("Value", style="white")
            table.add_row("Server URL", server_url)
            table.add_row("Mode", "Local Server" if is_local else "Remote Server")
            table.add_row("Status", "✅ Ready to connect")
            self.console.print(table)
        else:
            self._print_fallback_info("Connection Information", [
                ("Server URL", server_url),
                ("Mode", "Local Server" if is_local else "Remote Server"),
                ("Status", "✅ Ready to connect")
            ])
    
    def print_file_info(self, filename, size, server_url):
        """Print file information"""
        if RICH_AVAILABLE:
            table = Table(title="📁 File Information", box=box.ROUNDED)
            table.add_column("Property", style="bold cyan")
            table.add_column("Value", style="white")
            table.add_row("Filename", filename)
            table.add_row("Size", f"{size:,} bytes")
            table.add_row("Server", server_url)
            table.add_row("Status", "✅ Ready for upload")
            self.console.print(table)
        else:
            self._print_fallback_info("File Information", [
                ("Filename", filename),
                ("Size", f"{size:,} bytes"),
                ("Server", server_url),
                ("Status", "✅ Ready for upload")
            ])
    
    def print_local_ipsw_info(self, ipsw_filename, ipsw_size, ips_filename, ips_size, server_url):
        """Print information for local IPSW + IPS files"""
        if RICH_AVAILABLE:
            table = Table(title="📁 Local Files Information", box=box.ROUNDED)
            table.add_column("File Type", style="bold cyan")
            table.add_column("Filename", style="white")
            table.add_column("Size", style="white")
            table.add_column("Status", style="white")
            table.add_row("IPSW", ipsw_filename, f"{ipsw_size:,} bytes", "✅ Ready")
            table.add_row("IPS", ips_filename, f"{ips_size:,} bytes", "✅ Ready")
            table.add_row("Server", server_url, "-", "🌐 Connected")
            self.console.print(table)
        else:
            self._print_fallback_info("Local Files Information", [
                ("IPSW File", f"{ipsw_filename} ({ipsw_size:,} bytes)"),
                ("IPS File", f"{ips_filename} ({ips_size:,} bytes)"),
                ("Server", server_url),
                ("Status", "✅ Both files ready for processing")
            ])
    
    def _print_fallback_info(self, title, items):
        """Fallback info display"""
        if COLORAMA_AVAILABLE:
            print(f"\n{Fore.CYAN}{Style.BRIGHT}{title}:{Style.RESET_ALL}")
        else:
            print(f"\n{title}:")
        for key, value in items:
            if COLORAMA_AVAILABLE:
                print(f"  {Fore.YELLOW}{key}:{Style.RESET_ALL} {value}")
            else:
                print(f"  {key}: {value}")
    
    def print_success(self, message):
        """Print success message"""
        if RICH_AVAILABLE:
            self.console.print(f"✅ {message}", style="bold green")
        else:
            if COLORAMA_AVAILABLE:
                print(f"{Fore.GREEN}{Style.BRIGHT}✅ {message}{Style.RESET_ALL}")
            else:
                print(f"✅ {message}")
    
    def print_error(self, message):
        """Print error message"""
        if RICH_AVAILABLE:
            self.console.print(Panel(f"❌ {message}", style="bold red", title="Error"))
        else:
            if COLORAMA_AVAILABLE:
                print(f"{Fore.RED}{Style.BRIGHT}❌ Error: {message}{Style.RESET_ALL}")
            else:
                print(f"❌ Error: {message}")
    
    def print_warning(self, message):
        """Print warning message"""
        if RICH_AVAILABLE:
            self.console.print(f"⚠️  {message}", style="bold yellow")
        else:
            if COLORAMA_AVAILABLE:
                print(f"{Fore.YELLOW}{Style.BRIGHT}⚠️  {message}{Style.RESET_ALL}")
            else:
                print(f"⚠️  {message}")
    
    def print_device_info(self, file_info):
        """Print device and crash information"""
        if not file_info:
            return
            
        if RICH_AVAILABLE:
            table = Table(title="📱 Device & Crash Information", box=box.ROUNDED)
            table.add_column("Property", style="bold cyan", min_width=15)
            table.add_column("Value", style="white")
            
            # Device info
            if file_info.get('device_model'):
                table.add_row("Device", file_info['device_model'])
            if file_info.get('ios_version'):
                table.add_row("iOS Version", file_info['ios_version'])
            if file_info.get('build_version'):
                table.add_row("Build", file_info['build_version'])
            if file_info.get('process_name'):
                table.add_row("Process", file_info['process_name'])
            if file_info.get('bug_type'):
                table.add_row("Bug Type", file_info['bug_type'])
            
            file_type = "IPS Format" if file_info.get('is_ips_format') else "Text Format"
            table.add_row("File Type", file_type)
            
            self.console.print(table)
        else:
            info_items = []
            if file_info.get('device_model'):
                info_items.append(("Device", file_info['device_model']))
            if file_info.get('ios_version'):
                info_items.append(("iOS Version", file_info['ios_version']))
            if file_info.get('build_version'):
                info_items.append(("Build", file_info['build_version']))
            if file_info.get('process_name'):
                info_items.append(("Process", file_info['process_name']))
            if file_info.get('bug_type'):
                info_items.append(("Bug Type", file_info['bug_type']))
            
            file_type = "IPS Format" if file_info.get('is_ips_format') else "Text Format"
            info_items.append(("File Type", file_type))
            
            self._print_fallback_info("Device & Crash Information", info_items)
    
    def print_symbolicated_output(self, output, show_full=False, max_lines=50):
        """Print symbolicated output with syntax highlighting"""
        if not output:
            return
            
        lines = output.split('\n')
        if not show_full and len(lines) > max_lines:
            output = '\n'.join(lines[:max_lines]) + f'\n\n... (showing first {max_lines} lines, use --full for complete output)'
        
        if RICH_AVAILABLE:
            syntax = Syntax(output, "text", theme="monokai", line_numbers=True)
            self.console.print(Panel(
                syntax,
                title="🔍 Symbolicated Output",
                border_style="blue"
            ))
        else:
            if COLORAMA_AVAILABLE:
                print(f"\n{Fore.CYAN}{Style.BRIGHT}🔍 Symbolicated Output:{Style.RESET_ALL}")
            else:
                print("\n🔍 Symbolicated Output:")
            print(output)
    
    def print_summary(self, result, processing_time=None):
        """Print summary of results"""
        if RICH_AVAILABLE:
            summary_items = []
            
            if result.get('success'):
                summary_items.append(f"✅ {result.get('message', 'Symbolication completed')}")
            else:
                summary_items.append(f"❌ {result.get('message', 'Symbolication failed')}")
            
            if processing_time:
                summary_items.append(f"⏱️  Processing time: {processing_time:.2f} seconds")
            
            if result.get('analysis_id'):
                summary_items.append(f"🆔 Analysis ID: {result['analysis_id']}")
            
            if result.get('file_info'):
                file_info = result['file_info']
                if file_info.get('device_model'):
                    summary_items.append(f"📱 Device: {file_info['device_model']}")
                if file_info.get('ios_version'):
                    summary_items.append(f"🔧 iOS: {file_info['ios_version']}")
            
            self.console.print(Panel(
                "\n".join(summary_items),
                title="📋 Summary",
                border_style="green" if result.get('success') else "red"
            ))
        else:
            if COLORAMA_AVAILABLE:
                print(f"\n{Fore.CYAN}{Style.BRIGHT}📋 Summary:{Style.RESET_ALL}")
            else:
                print("\n📋 Summary:")
            
            if result.get('success'):
                if COLORAMA_AVAILABLE:
                    print(f"{Fore.GREEN}✅ {result.get('message', 'Symbolication completed')}{Style.RESET_ALL}")
                else:
                    print(f"✅ {result.get('message', 'Symbolication completed')}")
            else:
                if COLORAMA_AVAILABLE:
                    print(f"{Fore.RED}❌ {result.get('message', 'Symbolication failed')}{Style.RESET_ALL}")
                else:
                    print(f"❌ {result.get('message', 'Symbolication failed')}")
            
            if processing_time:
                print(f"⏱️  Processing time: {processing_time:.2f} seconds")
            
            if result.get('analysis_id'):
                print(f"🆔 Analysis ID: {result['analysis_id']}")

def detect_local_server():
    """Detect if local server is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def check_docker_running():
    """Check if Docker containers are running"""
    try:
        result = subprocess.run(['docker', 'ps', '--filter', 'name=ipsw', '--format', '{{.Names}}'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            containers = result.stdout.strip().split('\n')
            return len([c for c in containers if c.strip()]) >= 3  # At least 3 containers
    except:
        pass
    return False

def start_local_server(formatter):
    """Attempt to start local server"""
    if not check_docker_running():
        formatter.print_warning("Local IPSW Symbol Server not detected")
        formatter.print_warning("Attempting to start server...")
        
        try:
            # Try to start with docker compose
            result = subprocess.run(['docker', 'compose', 'up', '-d'], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                formatter.print_success("Local server started successfully!")
                # Wait a moment for services to be ready
                time.sleep(5)
                return True
            else:
                return False
        except:
            return False
    return True

def validate_file(filepath):
    """Validate file exists and is readable"""
    path = Path(filepath)
    if not path.exists():
        return False, f"File not found: {filepath}"
    if not path.is_file():
        return False, f"Not a file: {filepath}"
    if not os.access(path, os.R_OK):
        return False, f"File not readable: {filepath}"
    return True, None

def check_server_health(server_url):
    """Check if server is healthy"""
    try:
        response = requests.get(f"{server_url}/health", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Server returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to {server_url}"
    except Exception as e:
        return False, str(e)

def send_symbolication_request(server_url, filepath, formatter):
    """Send symbolication request to server"""
    start_time = time.time()
    
    try:
        # Validate file
        is_valid, error_msg = validate_file(filepath)
        if not is_valid:
            formatter.print_error(error_msg)
            return None
        
        path = Path(filepath)
        file_size = path.stat().st_size
        
        # Show file info
        formatter.print_file_info(path.name, file_size, server_url)
        
        # Show progress
        if RICH_AVAILABLE:
            with formatter.console.status("[bold green]Uploading and processing file...") as status:
                with open(path, 'rb') as f:
                    files = {'file': (path.name, f, 'application/octet-stream')}
                    response = requests.post(f"{server_url}/symbolicate", files=files, timeout=300)
        else:
            print("⏳ Uploading and processing file...")
            with open(path, 'rb') as f:
                files = {'file': (path.name, f, 'application/octet-stream')}
                response = requests.post(f"{server_url}/symbolicate", files=files, timeout=300)
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            formatter.print_success("File processed successfully!")
            return result, processing_time
        else:
            formatter.print_error(f"Server error: HTTP {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        formatter.print_error(f"Cannot connect to server: {server_url}")
        if "localhost" in server_url:
            formatter.print_error("Make sure the IPSW Symbol Server is running")
            formatter.print_error("Try: docker compose up -d")
        return None
    except requests.exceptions.Timeout:
        formatter.print_error("Request timeout - file processing took too long")
        return None
    except Exception as e:
        formatter.print_error(f"Unexpected error: {str(e)}")
        return None

def send_local_ipsw_request(server_url, ipsw_filepath, ips_filepath, formatter):
    """Send local IPSW + IPS symbolication request to server"""
    start_time = time.time()
    
    try:
        # Validate both files
        ipsw_valid, ipsw_error = validate_file(ipsw_filepath)
        if not ipsw_valid:
            formatter.print_error(f"IPSW file error: {ipsw_error}")
            return None
        
        ips_valid, ips_error = validate_file(ips_filepath)
        if not ips_valid:
            formatter.print_error(f"IPS file error: {ips_error}")
            return None
        
        ipsw_path = Path(ipsw_filepath)
        ips_path = Path(ips_filepath)
        ipsw_size = ipsw_path.stat().st_size
        ips_size = ips_path.stat().st_size
        
        # Show file info
        formatter.print_local_ipsw_info(ipsw_path.name, ipsw_size, ips_path.name, ips_size, server_url)
        
        # Determine which endpoint to use based on file size
        # Use streaming endpoint for files larger than 1GB
        large_file_threshold = 1024 * 1024 * 1024  # 1GB
        use_streaming = ipsw_size > large_file_threshold
        
        if use_streaming:
            endpoint = f"{server_url}/local-ipsw-symbolicate-stream"
            formatter.print_success(f"🚀 Using streaming upload for large IPSW file ({ipsw_size / (1024*1024*1024):.1f}GB)")
        else:
            endpoint = f"{server_url}/local-ipsw-symbolicate"
        
        # Show progress
        if RICH_AVAILABLE:
            status_message = "[bold green]Streaming large IPSW file..." if use_streaming else "[bold green]Uploading IPSW and IPS files, scanning, and symbolicating..."
            with formatter.console.status(status_message) as status:
                with open(ipsw_path, 'rb') as ipsw_f, open(ips_path, 'rb') as ips_f:
                    files = {
                        'ipsw_file': (ipsw_path.name, ipsw_f, 'application/octet-stream'),
                        'ips_file': (ips_path.name, ips_f, 'application/octet-stream')
                    }
                    # Increase timeout for large files
                    timeout = 3600 if use_streaming else 1800  # 60 min for streaming, 30 min for regular
                    response = requests.post(endpoint, files=files, timeout=timeout)
        else:
            status_message = "⏳ Streaming large IPSW file and symbolicating..." if use_streaming else "⏳ Uploading IPSW and IPS files, scanning, and symbolicating..."
            print(status_message)
            with open(ipsw_path, 'rb') as ipsw_f, open(ips_path, 'rb') as ips_f:
                files = {
                    'ipsw_file': (ipsw_path.name, ipsw_f, 'application/octet-stream'),
                    'ips_file': (ips_path.name, ips_f, 'application/octet-stream')
                }
                # Increase timeout for large files
                timeout = 3600 if use_streaming else 1800  # 60 min for streaming, 30 min for regular
                response = requests.post(endpoint, files=files, timeout=timeout)
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            success_message = "Streaming IPSW symbolication completed successfully!" if use_streaming else "Local IPSW symbolication completed successfully!"
            formatter.print_success(success_message)
            return result, processing_time
        else:
            formatter.print_error(f"Server error: HTTP {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        formatter.print_error(f"Cannot connect to server: {server_url}")
        if "localhost" in server_url:
            formatter.print_error("Make sure the IPSW Symbol Server is running")
        return None
    except requests.exceptions.Timeout:
        timeout_message = "Request timeout - large file streaming took too long (can take 30-60 minutes for 10GB+ files)" if 'use_streaming' in locals() and use_streaming else "Request timeout - processing took too long (large IPSW files can take 10-20 minutes)"
        formatter.print_error(timeout_message)
        return None
    except Exception as e:
        formatter.print_error(f"Unexpected error: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="IPSW Symbol Server CLI - Unified Local & Network Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic symbolication (auto-detect local/remote)
  ipsw-cli crash.ips
  
  # Local IPSW + IPS symbolication
  ipsw-cli --local-ipsw firmware.ipsw crash.ips
  
  # Connect to remote server
  ipsw-cli --server http://10.100.102.17:8000 crash.ips
  
  # Remote with local IPSW
  ipsw-cli --server http://192.168.1.100:8000 --local-ipsw firmware.ipsw crash.ips
  
  # Check server status
  ipsw-cli --check
  ipsw-cli --server http://10.100.102.17:8000 --check
  
  # Show complete output
  ipsw-cli --full crash.ips
        """
    )
    
    parser.add_argument('file', nargs='?', help='IPS crash file to symbolicate')
    parser.add_argument('--server', '-s', 
                       help='IPSW Symbol Server URL (auto-detects localhost if not specified)')
    parser.add_argument('--local-ipsw', help='Use local IPSW file instead of S3')
    parser.add_argument('--check', action='store_true', help='Check server status')
    parser.add_argument('--full', '-f', action='store_true', 
                       help='Show complete symbolicated output (not truncated)')
    parser.add_argument('--save', '-o', help='Save result to JSON file')
    parser.add_argument('--quiet', '-q', action='store_true', 
                       help='Minimal output mode')
    parser.add_argument('--no-banner', action='store_true', 
                       help='Skip banner display')
    parser.add_argument('--no-autostart', action='store_true',
                       help='Do not attempt to start local server automatically')
    
    args = parser.parse_args()
    
    # Determine server URL and mode
    if args.server:
        server_url = args.server.rstrip('/')
        is_local_server = 'localhost' in server_url or '127.0.0.1' in server_url
        mode = "local" if is_local_server else "network"
    else:
        # Auto-detect local server
        if detect_local_server():
            server_url = "http://localhost:8000"
            is_local_server = True
            mode = "local"
        else:
            # Try to start local server if not disabled
            if not args.no_autostart:
                formatter_temp = IPSWCLIFormatter("local")
                if start_local_server(formatter_temp):
                    if detect_local_server():
                        server_url = "http://localhost:8000"
                        is_local_server = True
                        mode = "local"
                    else:
                        print("❌ Failed to start local server. Please specify --server URL for remote access.")
                        sys.exit(1)
                else:
                    print("❌ Cannot start local server. Please specify --server URL for remote access.")
                    sys.exit(1)
            else:
                print("❌ No server specified and auto-start disabled. Use --server URL")
                sys.exit(1)
    
    # Initialize formatter with detected mode
    formatter = IPSWCLIFormatter(mode)
    
    # Show banner unless disabled
    if not args.no_banner:
        formatter.print_banner()
    
    # Check server health
    server_ok, server_info = check_server_health(server_url)
    if not server_ok:
        formatter.print_error(f"Server check failed: {server_info}")
        sys.exit(1)
    
    if not args.quiet:
        formatter.print_success(f"Connected to server: {server_url}")
    
    # Handle check-only mode
    if args.check:
        if RICH_AVAILABLE:
            table = Table(title="🔍 Server Status", box=box.ROUNDED)
            table.add_column("Property", style="bold cyan")
            table.add_column("Value", style="white")
            table.add_row("URL", server_url)
            table.add_row("Mode", "Local Server" if is_local_server else "Remote Server")
            table.add_row("Status", "✅ Online")
            table.add_row("Response", server_info.get('status', 'Unknown'))
            table.add_row("Timestamp", server_info.get('timestamp', 'Unknown'))
            formatter.console.print(table)
        else:
            formatter._print_fallback_info("Server Status", [
                ("URL", server_url),
                ("Mode", "Local Server" if is_local_server else "Remote Server"),
                ("Status", "✅ Online"),
                ("Response", server_info.get('status', 'Unknown')),
                ("Timestamp", server_info.get('timestamp', 'Unknown'))
            ])
        return
    
    # Handle local IPSW mode
    if args.local_ipsw:
        if not args.file:
            formatter.print_error("Local IPSW mode requires both IPSW and IPS files")
            formatter.print_error("Usage: ipsw-cli --local-ipsw firmware.ipsw crash.ips")
            sys.exit(1)
        
        # Validate IPSW file extension
        if not args.local_ipsw.lower().endswith('.ipsw'):
            formatter.print_error("Local IPSW file must have .ipsw extension")
            sys.exit(1)
        
        # Send local IPSW request
        result_data = send_local_ipsw_request(server_url, args.local_ipsw, args.file, formatter)
        if not result_data:
            sys.exit(1)
        
        result, processing_time = result_data
        
    else:
        # Standard symbolication mode
        if not args.file:
            formatter.print_error("Please provide a crash file to symbolicate")
            formatter.print_error("Usage: ipsw-cli crash.ips")
            sys.exit(1)
        
        # Send standard request
        result_data = send_symbolication_request(server_url, args.file, formatter)
        if not result_data:
            sys.exit(1)
        
        result, processing_time = result_data
    
    # Process results
    if result.get('success'):
        # Show device info
        if not args.quiet and result.get('file_info'):
            formatter.print_device_info(result['file_info'])
        
        # Show symbolicated output
        if result.get('symbolicated_output'):
            formatter.print_symbolicated_output(
                result['symbolicated_output'], 
                show_full=args.full
            )
        
        # Save results if requested
        if args.save:
            try:
                with open(args.save, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                formatter.print_success(f"Results saved to {args.save}")
            except Exception as e:
                formatter.print_error(f"Failed to save results: {e}")
        
        # Show summary
        if not args.quiet:
            formatter.print_summary(result, processing_time)
        
    else:
        # Show error
        formatter.print_error(result.get('message', 'Unknown error occurred'))
        if not args.quiet:
            formatter.print_summary(result, processing_time)
        sys.exit(1)

if __name__ == "__main__":
    main() 