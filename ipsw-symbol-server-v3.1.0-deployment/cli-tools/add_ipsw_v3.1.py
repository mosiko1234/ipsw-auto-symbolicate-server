#!/usr/bin/env python3
"""
🗄️ IPSW Symbol Server v3.1.0 - Enhanced IPSW Management Tool
Professional IPSW file management with symbol extraction
"""

import argparse
import requests
import json
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime
import time

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
PHONE = '📱'
LIGHTNING = '⚡'
DATABASE = '🗄️'
MAGNIFYING = '🔍'
SPARKLE = '✨'
PACKAGE = '📦'
EXTRACTION = '🔧'

class IPSWManager:
    def __init__(self, server_url="http://localhost:8082"):
        self.server_url = server_url
        self.version = "3.1.0"
        self.ipsw_dir = Path("./ipsw_files")
    
    def print_banner(self):
        """Print beautiful banner"""
        print(f"{Colors.BOLD}{Colors.BLUE}")
        print("╔═════════════════════════════════════════════════════════════════════════════╗")
        print(f"║                  {PACKAGE} IPSW Symbol Server v{self.version} {PACKAGE}                    ║")
        print("║                    Professional IPSW File Management                       ║")
        print("║                   Enhanced Symbol Extraction Technology                    ║")
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
                print(f"  {Colors.WHITE}• Current Symbols: {Colors.BOLD}{Colors.GREEN}{symbols_count:,}{Colors.NC}{Colors.WHITE} symbols{Colors.NC}")
                
                return True
            else:
                self.log_error(f"Server responded with status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_error(f"Server not available at {self.server_url}")
            print(f"{Colors.YELLOW}{INFO} Start server with: {Colors.BOLD}docker-compose up -d{Colors.NC}")
            return False
    
    def copy_ipsw_file(self, ipsw_path):
        """Copy IPSW file to system directory"""
        if not os.path.exists(ipsw_path):
            self.log_error(f"IPSW file not found: {ipsw_path}")
            return None
        
        filename = os.path.basename(ipsw_path)
        file_size = os.path.getsize(ipsw_path)
        
        self.log_progress("Copying IPSW file to system...")
        print(f"{Colors.CYAN}{FILE} File Information:{Colors.NC}")
        print(f"  {Colors.WHITE}• Name: {Colors.BOLD}{filename}{Colors.NC}")
        print(f"  {Colors.WHITE}• Size: {Colors.BOLD}{file_size:,}{Colors.NC}{Colors.WHITE} bytes (~{file_size // (1024**3)} GB){Colors.NC}")
        print(f"  {Colors.WHITE}• Destination: {Colors.BOLD}{self.ipsw_dir}/{filename}{Colors.NC}")
        
        # Create directory if it doesn't exist
        self.ipsw_dir.mkdir(exist_ok=True)
        
        try:
            dest_path = self.ipsw_dir / filename
            shutil.copy2(ipsw_path, dest_path)
            self.log_success("File copied successfully")
            return filename
        except Exception as e:
            self.log_error(f"Failed to copy file: {e}")
            return None
    
    def verify_ipsw_detection(self, filename):
        """Verify IPSW file is detected by server"""
        self.log_progress("Verifying IPSW file detection...")
        time.sleep(3)  # Give server time to detect
        
        try:
            response = requests.get(f"{self.server_url}/v1/ipsw/list", timeout=10)
            if response.status_code == 200:
                ipsw_data = response.json()
                ipsw_files = ipsw_data.get('ipsw_files', [])
                
                # Find our file
                detected_file = None
                for ipsw in ipsw_files:
                    if ipsw.get('filename') == filename:
                        detected_file = ipsw
                        break
                
                if detected_file:
                    self.log_success("IPSW file detected and cataloged")
                    
                    print(f"{Colors.CYAN}{PHONE} Device Information:{Colors.NC}")
                    print(f"  {Colors.WHITE}• Device: {Colors.BOLD}{detected_file.get('device_model', 'unknown')}{Colors.NC}")
                    print(f"  {Colors.WHITE}• iOS Version: {Colors.BOLD}{detected_file.get('os_version', 'unknown')}{Colors.NC}")
                    print(f"  {Colors.WHITE}• Build ID: {Colors.BOLD}{detected_file.get('build_id', 'unknown')}{Colors.NC}")
                    print(f"  {Colors.WHITE}• File Size: {Colors.BOLD}{detected_file.get('size', 'unknown')}{Colors.NC}{Colors.WHITE} bytes{Colors.NC}")
                    
                    return True
                else:
                    self.log_error("IPSW file not detected in system")
                    return False
            else:
                self.log_error(f"Failed to get IPSW list: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error(f"Error checking detection: {e}")
            return False
    
    def scan_ipsw_with_extraction(self, filename, extract_symbols=True):
        """Scan IPSW file with optional symbol extraction"""
        ipsw_path = f"/app/ipsw_files/{filename}"
        
        self.log_progress("Scanning IPSW file and preparing for symbol extraction...")
        
        scan_data = {
            "path": ipsw_path,
            "extract_symbols": extract_symbols
        }
        
        if extract_symbols:
            print(f"{Colors.CYAN}{EXTRACTION} Symbol Extraction: {Colors.BOLD}{Colors.GREEN}ENABLED{Colors.NC}")
        else:
            print(f"{Colors.CYAN}{EXTRACTION} Symbol Extraction: {Colors.BOLD}{Colors.YELLOW}DISABLED{Colors.NC}")
        
        try:
            response = requests.post(
                f"{self.server_url}/v1/syms/scan",
                json=scan_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'unknown')
                scan_id = result.get('scan_id', 'unknown')
                
                print(f"{Colors.CYAN}{CHART} Scan Results:{Colors.NC}")
                print(json.dumps(result, indent=2))
                
                if status == 'completed':
                    self.log_success("IPSW scan completed successfully!")
                    
                    if extract_symbols and scan_id != 'unknown':
                        self.log_info(f"Symbol extraction initiated in background (Scan ID: {scan_id})")
                        self.monitor_extraction_progress(scan_id)
                    
                    return True
                else:
                    self.log_warning("Scan completed with issues - check results above")
                    return False
            else:
                self.log_error(f"Scan failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error(f"Scan error: {e}")
            return False
    
    def monitor_extraction_progress(self, scan_id):
        """Monitor symbol extraction progress"""
        print()
        self.log_progress("Monitoring symbol extraction progress...")
        
        max_checks = 30
        check_count = 0
        
        while check_count < max_checks:
            try:
                response = requests.get(f"{self.server_url}/v1/syms/scans")
                if response.status_code == 200:
                    scans_data = response.json()
                    scans = scans_data.get('scans', [])
                    
                    # Find our scan
                    scan = None
                    for s in scans:
                        if s.get('id') == scan_id:
                            scan = s
                            break
                    
                    if scan:
                        status = scan.get('status', 'unknown')
                        if status == 'extracting_symbols':
                            print(f"\r{Colors.PURPLE}{GEAR} Extracting symbols... ({check_count}/{max_checks}){Colors.NC}", end='', flush=True)
                        elif status == 'completed':
                            print(f"\r{Colors.GREEN}{CHECK} Symbol extraction completed!{Colors.NC}")
                            self.show_extraction_summary(scan_id, scan)
                            return True
                        elif status == 'failed':
                            print(f"\r{Colors.RED}{CROSS} Symbol extraction failed{Colors.NC}")
                            return False
                        else:
                            print(f"\r{Colors.YELLOW}{WARNING} Unknown status: {status}{Colors.NC}", end='', flush=True)
                
                time.sleep(5)
                check_count += 1
                
            except Exception as e:
                print(f"\r{Colors.RED}{CROSS} Error monitoring: {e}{Colors.NC}")
                return False
        
        print(f"\r{Colors.YELLOW}{WARNING} Extraction monitoring timeout - check manually{Colors.NC}")
        return False
    
    def show_extraction_summary(self, scan_id, scan_data):
        """Show extraction summary"""
        symbols_extracted = scan_data.get('symbols_extracted', 0)
        
        print(f"{Colors.CYAN}{DATABASE} Extraction Summary:{Colors.NC}")
        print(f"  {Colors.WHITE}• Scan ID: {Colors.BOLD}{scan_id}{Colors.NC}")
        print(f"  {Colors.WHITE}• Symbols Extracted: {Colors.BOLD}{Colors.GREEN}{symbols_extracted:,}{Colors.NC}{Colors.WHITE} symbols{Colors.NC}")
        print(f"  {Colors.WHITE}• Status: {Colors.BOLD}{Colors.GREEN}Completed{Colors.NC}")
        
        # Get updated database stats
        try:
            response = requests.get(f"{self.server_url}/v1/syms/stats")
            if response.status_code == 200:
                stats = response.json()
                total_symbols = stats.get('total_symbols', 0)
                
                print(f"{Colors.CYAN}{CHART} Updated Database Statistics:{Colors.NC}")
                print(f"  {Colors.WHITE}• Total Symbols: {Colors.BOLD}{Colors.GREEN}{total_symbols:,}{Colors.NC}{Colors.WHITE} symbols{Colors.NC}")
                self.log_success("Database ready for ultra-fast symbolication!")
        except:
            pass
    
    def show_final_summary(self, filename, extract_enabled):
        """Show final summary"""
        print()
        print(f"{Colors.GREEN}{SPARKLE} {Colors.BOLD}IPSW Management Summary{Colors.NC}")
        print(f"{Colors.WHITE}" + "="*71 + f"{Colors.NC}")
        print(f"{Colors.WHITE}📦 IPSW File: {Colors.BOLD}{filename}{Colors.NC}")
        print(f"{Colors.WHITE}🗄️ Symbol Extraction: {Colors.BOLD}{Colors.GREEN if extract_enabled else Colors.YELLOW}{'Enabled' if extract_enabled else 'Disabled'}{Colors.NC}")
        print(f"{Colors.WHITE}⚡ Server: {Colors.BOLD}IPSW Symbol Server v{self.version}{Colors.NC}")
        print(f"{Colors.WHITE}🕐 Time: {Colors.BOLD}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.NC}")
        
        print()
        print(f"{Colors.CYAN}{INFO} {Colors.BOLD}System Commands:{Colors.NC}")
        print(f"  {Colors.WHITE}• List IPSWs:      {Colors.BOLD}curl {self.server_url}/v1/ipsw/list{Colors.NC}")
        print(f"  {Colors.WHITE}• Check scans:     {Colors.BOLD}curl {self.server_url}/v1/syms/scans{Colors.NC}")
        print(f"  {Colors.WHITE}• Symbol stats:    {Colors.BOLD}curl {self.server_url}/v1/syms/stats{Colors.NC}")
        print(f"  {Colors.WHITE}• Symbolicate:     {Colors.BOLD}./symbolicate_v3.1.py crash.ips{Colors.NC}")
        
        print()
        print(f"{Colors.GREEN}{CHECK} {Colors.BOLD}System ready for professional symbolication!{Colors.NC} {ROCKET}")
    
    def add_ipsw(self, ipsw_path, extract_symbols=True):
        """Main function to add IPSW file"""
        filename = self.copy_ipsw_file(ipsw_path)
        if not filename:
            return False
        
        print()
        if not self.verify_ipsw_detection(filename):
            return False
        
        print()
        if not self.scan_ipsw_with_extraction(filename, extract_symbols):
            return False
        
        self.show_final_summary(filename, extract_symbols)
        return True

def main():
    parser = argparse.ArgumentParser(
        description=f"{PACKAGE} IPSW Symbol Server v3.1.0 - Enhanced IPSW Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  add_ipsw_v3.1.py iPhone15,2_18.5_22F76_Restore.ipsw
  add_ipsw_v3.1.py iPhone15,2_18.5_22F76_Restore.ipsw --no-extract
  add_ipsw_v3.1.py iPhone15,2_18.5_22F76_Restore.ipsw --server http://192.168.1.100:8082
        """
    )
    
    parser.add_argument('ipsw_file', help='IPSW file to add')
    parser.add_argument('--no-extract', action='store_true', help='Skip symbol extraction')
    parser.add_argument('--server', default='http://localhost:8082', help='Server URL (default: http://localhost:8082)')
    
    args = parser.parse_args()
    
    manager = IPSWManager(args.server)
    manager.print_banner()
    
    print(f"{Colors.WHITE}{Colors.BOLD}Starting Enhanced IPSW Management{Colors.NC}")
    print(f"{Colors.GRAY}File: {os.path.basename(args.ipsw_file)} → Enhanced v3.1.0 Processing{Colors.NC}")
    print()
    
    # Check server health first
    if not manager.check_server_health():
        sys.exit(1)
    
    print()
    
    # Add IPSW file
    extract_symbols = not args.no_extract
    if manager.add_ipsw(args.ipsw_file, extract_symbols):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
