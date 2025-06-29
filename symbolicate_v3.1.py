#!/usr/bin/env python3
"""
🚀 IPSW Symbol Server v3.1.0 - Enhanced Symbolication Tool
Professional iOS Crash Symbolication with Database Symbols
"""

import argparse
import requests
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Colors for beautiful output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    GRAY = '\033[0;37m'
    NC = '\033[0m'
    BOLD = '\033[1m'

# Unicode symbols
ROCKET = '🚀'
CHECK = '✅'
CROSS = '❌'
WARNING = '⚠️'
INFO = 'ℹ️'
GEAR = '⚙️'
CHART = '📊'
FILE = '📁'
LIGHTNING = '⚡'
DATABASE = '🗄️'
MAGNIFYING = '🔍'
SPARKLE = '✨'

class IPSWSymbolicator:
    def __init__(self, server_url="http://localhost:8082"):
        self.server_url = server_url
        self.version = "3.1.0"
    
    def print_banner(self):
        """Print beautiful banner"""
        print(f"{Colors.BOLD}{Colors.BLUE}")
        print("╔═════════════════════════════════════════════════════════════════════════════╗")
        print(f"║                    {ROCKET} IPSW Symbol Server v{self.version} {ROCKET}                      ║")
        print("║                  Professional iOS Crash Symbolication                      ║")
        print("║                     Enhanced Database-First Technology                     ║")
        print("╚═════════════════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.NC}")
    
    def log_info(self, message):
        print(f"{Colors.BLUE}{INFO} {message}{Colors.NC}")
    
    def log_success(self, message):
        print(f"{Colors.GREEN}{CHECK} {message}{Colors.NC}")
    
    def log_warning(self, message):
        print(f"{Colors.YELLOW}{WARNING} {message}{Colors.NC}")
    
    def log_error(self, message):
        print(f"{Colors.RED}{CROSS} {message}{Colors.NC}")
    
    def log_progress(self, message):
        print(f"{Colors.PURPLE}{GEAR} {message}{Colors.NC}")
    
    def check_server_health(self):
        """Check server health and return status"""
        try:
            self.log_progress("Connecting to IPSW Symbol Server v3.1.0...")
            response = requests.get(f"{self.server_url}/health", timeout=5)
            
            if response.status_code == 200:
                self.log_success("Server connection established")
                health_data = response.json()
                
                version = health_data.get('version', 'unknown')
                symbols_count = health_data.get('symbols_in_database', 0)
                
                print(f"{Colors.CYAN}{DATABASE} Database Status:{Colors.NC}")
                print(f"  {Colors.WHITE}• Version: {version}{Colors.NC}")
                print(f"  {Colors.WHITE}• Symbols Available: {Colors.BOLD}{Colors.GREEN}{symbols_count:,}{Colors.NC}{Colors.WHITE} symbols{Colors.NC}")
                
                if symbols_count > 0:
                    self.log_success("v3.1.0 Database symbols ready for ultra-fast symbolication!")
                else:
                    self.log_warning("No symbols in database - will try IPSW fallback method")
                
                return True
            else:
                self.log_error(f"Server responded with status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_error(f"Server not available at {self.server_url}")
            print(f"{Colors.YELLOW}{INFO} Start server with: {Colors.BOLD}docker-compose up -d{Colors.NC}")
            return False
    
    def symbolicate_file(self, crashlog_path, output_path=None):
        """Symbolicate a crash file"""
        if not os.path.exists(crashlog_path):
            self.log_error(f"Crashlog file not found: {crashlog_path}")
            return False
        
        # Auto-generate output path if not provided
        if not output_path:
            base_name = Path(crashlog_path).stem
            output_path = f"{base_name}_symbolicated.txt"
        
        self.log_progress("Starting v3.1.0 enhanced symbolication...")
        
        # Show file info
        file_size = os.path.getsize(crashlog_path)
        print(f"{Colors.CYAN}{FILE} Input File Analysis:{Colors.NC}")
        print(f"  {Colors.WHITE}• File: {Colors.BOLD}{os.path.basename(crashlog_path)}{Colors.NC}")
        print(f"  {Colors.WHITE}• Size: {Colors.BOLD}{file_size:,}{Colors.NC}{Colors.WHITE} bytes{Colors.NC}")
        
        try:
            # Send symbolication request
            with open(crashlog_path, 'rb') as f:
                files = {'crashlog': f}
                response = requests.post(
                    f"{self.server_url}/v1/symbolicate",
                    files=files,
                    timeout=300
                )
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('symbolicated', False)
                method = result.get('method', 'unknown')
                symbols_used = result.get('symbols_used', 0)
                
                if success:
                    self.log_success("Symbolication completed successfully!")
                    
                    # Save result with enhanced header
                    with open(output_path, 'w') as f:
                        f.write(f"# {ROCKET} IPSW Symbol Server v{self.version} - Symbolication Result\n")
                        f.write(f"# Generated: {datetime.now()}\n")
                        f.write(f"# Method: {method}\n")
                        f.write(f"# Symbols Used: {symbols_used}\n")
                        f.write(f"# Input: {os.path.basename(crashlog_path)}\n")
                        f.write("# " + "="*64 + "\n\n")
                        f.write(result.get('output', ''))
                    
                    self.log_success(f"Result saved to: {Colors.BOLD}{output_path}{Colors.NC}")
                    
                    # Show symbolication details
                    print(f"{Colors.CYAN}{LIGHTNING} Symbolication Details:{Colors.NC}")
                    print(f"  {Colors.WHITE}• Method: {Colors.BOLD}{Colors.GREEN}{method}{Colors.NC}")
                    
                    if method == 'database_symbols':
                        print(f"  {Colors.WHITE}• Performance: {Colors.BOLD}{Colors.GREEN}Ultra-fast database lookup{Colors.NC} {LIGHTNING}")
                        print(f"  {Colors.WHITE}• Symbols Used: {Colors.BOLD}{Colors.GREEN}{symbols_used:,}{Colors.NC}{Colors.WHITE} symbols{Colors.NC}")
                        print(f"  {Colors.WHITE}• Technology: {Colors.BOLD}{Colors.PURPLE}v3.1.0 Database-First Architecture{Colors.NC}")
                    else:
                        print(f"  {Colors.WHITE}• Performance: {Colors.BOLD}{Colors.YELLOW}IPSW file processing{Colors.NC}")
                        print(f"  {Colors.WHITE}• Note: {Colors.YELLOW}Consider symbol extraction for faster future processing{Colors.NC}")
                    
                    self.show_result_preview(output_path)
                    self.show_summary(crashlog_path, output_path)
                    return True
                else:
                    self.log_error("Symbolication failed!")
                    error = result.get('error', 'unknown error')
                    print(f"{Colors.RED}Error Details: {error}{Colors.NC}")
                    return False
            else:
                self.log_error(f"Server error: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error(f"Error during symbolication: {str(e)}")
            return False
    
    def show_result_preview(self, file_path):
        """Show preview of symbolicated output"""
        print()
        print(f"{Colors.CYAN}{MAGNIFYING} Result Preview:{Colors.NC}")
        print(f"{Colors.WHITE}" + "="*68 + f"{Colors.NC}")
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:15], 1):
                    print(f"{i:2}: {line.rstrip()}")
                
                if len(lines) > 15:
                    print(f"{Colors.GRAY}... ({len(lines)} total lines - see full file){Colors.NC}")
        except Exception as e:
            self.log_error(f"Could not preview file: {e}")
        
        print(f"{Colors.WHITE}" + "="*68 + f"{Colors.NC}")
    
    def show_summary(self, input_path, output_path):
        """Show comprehensive summary"""
        print()
        print(f"{Colors.GREEN}{SPARKLE} {Colors.BOLD}Symbolication Summary{Colors.NC}")
        print(f"{Colors.WHITE}" + "="*71 + f"{Colors.NC}")
        
        input_size = os.path.getsize(input_path)
        output_size = os.path.getsize(output_path)
        
        with open(output_path, 'r') as f:
            output_lines = len(f.readlines())
        
        print(f"{Colors.WHITE}📥 Input:  {Colors.BOLD}{os.path.basename(input_path)}{Colors.NC}{Colors.WHITE} ({input_size:,} bytes){Colors.NC}")
        print(f"{Colors.WHITE}📤 Output: {Colors.BOLD}{os.path.basename(output_path)}{Colors.NC}{Colors.WHITE} ({output_size:,} bytes, {output_lines:,} lines){Colors.NC}")
        print(f"{Colors.WHITE}⚡ Server: {Colors.BOLD}IPSW Symbol Server v{self.version}{Colors.NC}")
        print(f"{Colors.WHITE}🕐 Time:   {Colors.BOLD}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.NC}")
        
        print()
        print(f"{Colors.CYAN}{INFO} {Colors.BOLD}Quick Actions:{Colors.NC}")
        print(f"  {Colors.WHITE}• View result:     {Colors.BOLD}cat '{output_path}'{Colors.NC}")
        print(f"  {Colors.WHITE}• Edit result:     {Colors.BOLD}code '{output_path}'{Colors.NC}")
        print(f"  {Colors.WHITE}• Search symbols:  {Colors.BOLD}grep 'function_name' '{output_path}'{Colors.NC}")
        print(f"  {Colors.WHITE}• Delete result:   {Colors.BOLD}rm '{output_path}'{Colors.NC}")
        
        print()
        print(f"{Colors.GREEN}{CHECK} {Colors.BOLD}Symbolication completed successfully!{Colors.NC} {SPARKLE}")

def main():
    parser = argparse.ArgumentParser(
        description=f"{ROCKET} IPSW Symbol Server v3.1.0 - Enhanced Symbolication Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  symbolicate_v3.1.py crash.ips
  symbolicate_v3.1.py crash.ips -o symbolicated_crash.txt
  symbolicate_v3.1.py MyApp-crash.ips --server http://192.168.1.100:8082
        """
    )
    
    parser.add_argument('crashlog', help='Crash file to symbolicate')
    parser.add_argument('-o', '--output', help='Output file path (auto-generated if not specified)')
    parser.add_argument('--server', default='http://localhost:8082', help='Server URL (default: http://localhost:8082)')
    
    args = parser.parse_args()
    
    symbolicator = IPSWSymbolicator(args.server)
    symbolicator.print_banner()
    
    print(f"{Colors.WHITE}{Colors.BOLD}Starting Enhanced Symbolication{Colors.NC}")
    print(f"{Colors.GRAY}File: {os.path.basename(args.crashlog)} → {os.path.basename(args.output or 'auto-generated')}{Colors.NC}")
    print()
    
    # Check server health first
    if not symbolicator.check_server_health():
        sys.exit(1)
    
    print()
    
    # Perform symbolication
    if symbolicator.symbolicate_file(args.crashlog, args.output):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
