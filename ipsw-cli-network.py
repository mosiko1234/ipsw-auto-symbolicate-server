#!/usr/bin/env python3
"""
IPSW Symbol Server CLI - Network Client
For connecting to remote IPSW Symbol Server from any machine
"""

import argparse
import requests
import json
import sys
import os
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

class NetworkIPSWCLI:
    """Network CLI for remote IPSW Symbol Server"""
    
    def __init__(self, server_url):
        self.server_url = server_url.rstrip('/')
        self.console = Console() if RICH_AVAILABLE else None
        
    def print_banner(self):
        """Print a beautiful banner"""
        if RICH_AVAILABLE:
            banner = """
╔═══════════════════════════════════════════════════════════════╗
║              🌐 IPSW Symbol Server CLI - Network              ║
║              Professional iOS Crash Symbolication            ║
║                     Remote Server Client                     ║
╚═══════════════════════════════════════════════════════════════╝
"""
            self.console.print(Panel(
                Align.center(banner.strip()),
                style="bold blue",
                box=box.DOUBLE
            ))
        else:
            print("=" * 65)
            print("🌐 IPSW Symbol Server CLI - Network Client")
            print("=" * 65)
    
    def print_success(self, message):
        """Print success message"""
        if RICH_AVAILABLE:
            self.console.print(f"✅ {message}", style="bold green")
        else:
            print(f"✅ {message}")
    
    def print_error(self, message):
        """Print error message"""
        if RICH_AVAILABLE:
            self.console.print(Panel(f"❌ {message}", style="bold red", title="Error"))
        else:
            print(f"❌ Error: {message}")
    
    def print_info(self, title, items):
        """Print information table"""
        if RICH_AVAILABLE:
            table = Table(title=title, box=box.ROUNDED)
            table.add_column("Property", style="bold cyan")
            table.add_column("Value", style="white")
            for key, value in items:
                table.add_row(key, str(value))
            self.console.print(table)
        else:
            print(f"\n{title}:")
            for key, value in items:
                print(f"  {key}: {value}")
    
    def check_server(self):
        """Check if server is accessible"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Server returned status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, f"Cannot connect to {self.server_url}"
        except Exception as e:
            return False, str(e)
    
    def upload_crash_file(self, filepath):
        """Upload and symbolicate crash file"""
        try:
            # Validate file
            path = Path(filepath)
            if not path.exists():
                self.print_error(f"File not found: {filepath}")
                return None
            
            file_size = path.stat().st_size
            self.print_info("📁 File Information", [
                ("Filename", path.name),
                ("Size", f"{file_size:,} bytes"),
                ("Server", self.server_url),
                ("Status", "✅ Ready for upload")
            ])
            
            # Upload file
            if RICH_AVAILABLE:
                with self.console.status("[bold green]Uploading and processing file...") as status:
                    with open(path, 'rb') as f:
                        files = {'file': (path.name, f, 'application/octet-stream')}
                        response = requests.post(f"{self.server_url}/symbolicate", files=files, timeout=300)
            else:
                print("⏳ Uploading and processing file...")
                with open(path, 'rb') as f:
                    files = {'file': (path.name, f, 'application/octet-stream')}
                    response = requests.post(f"{self.server_url}/symbolicate", files=files, timeout=300)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.print_error(f"Server error: HTTP {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.print_error(f"Upload failed: {str(e)}")
            return None
    
    def upload_local_ipsw(self, ipsw_filepath, ips_filepath):
        """Upload IPSW and IPS files for symbolication"""
        try:
            ipsw_path = Path(ipsw_filepath)
            ips_path = Path(ips_filepath)
            
            if not ipsw_path.exists():
                self.print_error(f"IPSW file not found: {ipsw_filepath}")
                return None
            
            if not ips_path.exists():
                self.print_error(f"IPS file not found: {ips_filepath}")
                return None
            
            ipsw_size = ipsw_path.stat().st_size
            ips_size = ips_path.stat().st_size
            
            self.print_info("📁 Local Files Information", [
                ("IPSW File", f"{ipsw_path.name} ({ipsw_size:,} bytes)"),
                ("IPS File", f"{ips_path.name} ({ips_size:,} bytes)"),
                ("Server", self.server_url),
                ("Status", "✅ Ready for upload")
            ])
            
            # Choose endpoint based on file size
            large_file_threshold = 1024 * 1024 * 1024  # 1GB
            use_streaming = ipsw_size > large_file_threshold
            
            if use_streaming:
                endpoint = f"{self.server_url}/local-ipsw-symbolicate-stream"
                self.print_success(f"🚀 Using streaming upload for large IPSW file ({ipsw_size / (1024*1024*1024):.1f}GB)")
                timeout = 3600  # 60 minutes
            else:
                endpoint = f"{self.server_url}/local-ipsw-symbolicate"
                timeout = 1800  # 30 minutes
            
            # Upload files
            if RICH_AVAILABLE:
                status_msg = "[bold green]Streaming large IPSW..." if use_streaming else "[bold green]Uploading files..."
                with self.console.status(status_msg) as status:
                    with open(ipsw_path, 'rb') as ipsw_f, open(ips_path, 'rb') as ips_f:
                        files = {
                            'ipsw_file': (ipsw_path.name, ipsw_f, 'application/octet-stream'),
                            'ips_file': (ips_path.name, ips_f, 'application/octet-stream')
                        }
                        response = requests.post(endpoint, files=files, timeout=timeout)
            else:
                status_msg = "⏳ Streaming large IPSW..." if use_streaming else "⏳ Uploading files..."
                print(status_msg)
                with open(ipsw_path, 'rb') as ipsw_f, open(ips_path, 'rb') as ips_f:
                    files = {
                        'ipsw_file': (ipsw_path.name, ipsw_f, 'application/octet-stream'),
                        'ips_file': (ips_path.name, ips_f, 'application/octet-stream')
                    }
                    response = requests.post(endpoint, files=files, timeout=timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.print_error(f"Server error: HTTP {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            self.print_error("Upload timeout - large files can take 30-60 minutes")
            return None
        except Exception as e:
            self.print_error(f"Upload failed: {str(e)}")
            return None
    
    def print_results(self, result):
        """Print symbolication results"""
        if not result:
            return
        
        # Device info
        if result.get('file_info'):
            file_info = result['file_info']
            device_items = []
            if file_info.get('device_model'):
                device_items.append(("Device", file_info['device_model']))
            if file_info.get('ios_version'):
                device_items.append(("iOS Version", file_info['ios_version']))
            if file_info.get('build_version'):
                device_items.append(("Build", file_info['build_version']))
            if file_info.get('process_name'):
                device_items.append(("Process", file_info['process_name']))
            
            if device_items:
                self.print_info("📱 Device & Crash Information", device_items)
        
        # Show symbolicated output
        if result.get('symbolicated_output'):
            output = result['symbolicated_output']
            lines = output.split('\n')
            if len(lines) > 50:
                output = '\n'.join(lines[:50]) + '\n\n... (truncated, use --full for complete output)'
            
            if RICH_AVAILABLE:
                syntax = Syntax(output, "text", theme="monokai", line_numbers=True)
                self.console.print(Panel(
                    syntax,
                    title="🔍 Symbolicated Output",
                    border_style="blue"
                ))
            else:
                print("\n🔍 Symbolicated Output:")
                print(output)
        
        # Summary
        success = result.get('success', False)
        message = result.get('message', 'Unknown result')
        
        if RICH_AVAILABLE:
            style = "green" if success else "red"
            icon = "✅" if success else "❌"
            self.console.print(Panel(
                f"{icon} {message}",
                title="📋 Summary",
                border_style=style
            ))
        else:
            icon = "✅" if success else "❌"
            print(f"\n📋 Summary: {icon} {message}")

def main():
    parser = argparse.ArgumentParser(
        description="IPSW Symbol Server CLI - Network Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic symbolication
  ipsw-cli-network --server http://10.100.102.17:8000 crash.ips
  
  # Local IPSW + IPS symbolication
  ipsw-cli-network --server http://10.100.102.17:8000 --local-ipsw firmware.ipsw crash.ips
  
  # Check server status
  ipsw-cli-network --server http://10.100.102.17:8000 --check
        """
    )
    
    parser.add_argument('file', nargs='?', help='IPS crash file to symbolicate')
    parser.add_argument('--server', '-s', required=True,
                       help='IPSW Symbol Server URL (e.g., http://10.100.102.17:8000)')
    parser.add_argument('--local-ipsw', help='Use local IPSW file instead of S3')
    parser.add_argument('--check', action='store_true', help='Check server status')
    parser.add_argument('--full', '-f', action='store_true', help='Show complete output')
    parser.add_argument('--no-banner', action='store_true', help='Skip banner')
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = NetworkIPSWCLI(args.server)
    
    # Show banner
    if not args.no_banner:
        cli.print_banner()
    
    # Check server
    server_ok, server_info = cli.check_server()
    if not server_ok:
        cli.print_error(f"Server check failed: {server_info}")
        sys.exit(1)
    
    cli.print_success(f"Connected to server: {args.server}")
    
    # Handle check-only mode
    if args.check:
        cli.print_info("🔍 Server Status", [
            ("URL", args.server),
            ("Status", "✅ Online"),
            ("Response", server_info.get('status', 'Unknown')),
            ("Timestamp", server_info.get('timestamp', 'Unknown'))
        ])
        return
    
    # Handle symbolication
    if args.local_ipsw:
        if not args.file:
            cli.print_error("Local IPSW mode requires both IPSW and IPS files")
            sys.exit(1)
        
        result = cli.upload_local_ipsw(args.local_ipsw, args.file)
    else:
        if not args.file:
            cli.print_error("Please provide a crash file to symbolicate")
            sys.exit(1)
        
        result = cli.upload_crash_file(args.file)
    
    if result:
        cli.print_results(result)
        if not result.get('success'):
            sys.exit(1)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 