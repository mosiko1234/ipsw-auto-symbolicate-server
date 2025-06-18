#!/usr/bin/env python3
"""
IPSW Symbol Server CLI Tool
Beautiful terminal interface for symbolication requests
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

class IPSWCLIFormatter:
    """Beautiful terminal formatter for IPSW symbolication results"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        
    def print_banner(self):
        """Print a beautiful banner"""
        if RICH_AVAILABLE:
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
        print("🚀 IPSW Symbol Server CLI - Professional iOS Crash Symbolication")
        print("=" * 65)
        if COLORAMA_AVAILABLE:
            print(f"{Style.RESET_ALL}")
    
    def print_file_info(self, filename, size):
        """Print file information"""
        if RICH_AVAILABLE:
            table = Table(title="📁 File Information", box=box.ROUNDED)
            table.add_column("Property", style="bold cyan")
            table.add_column("Value", style="white")
            table.add_row("Filename", filename)
            table.add_row("Size", f"{size:,} bytes")
            table.add_row("Status", "✅ Ready for upload")
            self.console.print(table)
        else:
            self._print_fallback_info("File Information", [
                ("Filename", filename),
                ("Size", f"{size:,} bytes"),
                ("Status", "✅ Ready for upload")
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
    
    def print_symbolication_stats(self, symbolicated_output):
        """Print symbolication statistics"""
        if not symbolicated_output:
            return
            
        lines = symbolicated_output.split('\n')
        symbol_lines = len([l for l in lines if '+' in l and '<unknown>' not in l])
        unknown_lines = len([l for l in lines if '<unknown>' in l])
        total_addresses = len([l for l in lines if '+' in l])
        kernel_addresses = symbolicated_output.count('0xfffffff')
        
        success_rate = (symbol_lines / total_addresses * 100) if total_addresses > 0 else 0
        
        if RICH_AVAILABLE:
            table = Table(title="📊 Symbolication Statistics", box=box.ROUNDED)
            table.add_column("Metric", style="bold cyan")
            table.add_column("Count", style="white", justify="right")
            table.add_column("Status", style="white")
            
            table.add_row("Symbols Found", str(symbol_lines), "✅")
            table.add_row("Unknown Symbols", str(unknown_lines), "❓")
            table.add_row("Kernel Addresses", str(kernel_addresses), "🔧")
            
            if success_rate >= 80:
                status_text = "Excellent"
            elif success_rate >= 50:
                status_text = "Good"
            else:
                status_text = "Poor"
            
            table.add_row("Success Rate", f"{success_rate:.1f}%", status_text)
            
            self.console.print(table)
        else:
            status_text = "Excellent" if success_rate >= 80 else "Good" if success_rate >= 50 else "Poor"
            
            self._print_fallback_info("Symbolication Statistics", [
                ("Symbols Found", f"{symbol_lines} ✅"),
                ("Unknown Symbols", f"{unknown_lines} ❓"),
                ("Kernel Addresses", f"{kernel_addresses} 🔧"),
                ("Success Rate", f"{success_rate:.1f}% ({status_text})")
            ])
    
    def print_symbolicated_output(self, output, show_full=False, max_lines=50):
        """Print symbolicated output with syntax highlighting"""
        if not output:
            return
            
        lines = output.split('\n')
        
        if RICH_AVAILABLE:
            if show_full or len(lines) <= max_lines:
                syntax = Syntax(output, "text", theme="monokai", line_numbers=True)
                panel = Panel(syntax, title="🔍 Symbolicated Output", box=box.ROUNDED)
                self.console.print(panel)
            else:
                # Show preview
                preview = '\n'.join(lines[:max_lines])
                syntax = Syntax(preview, "text", theme="monokai", line_numbers=True)
                panel = Panel(
                    syntax, 
                    title=f"🔍 Symbolicated Output (First {max_lines} lines)",
                    subtitle=f"Total: {len(lines)} lines - Use --full to see complete output",
                    box=box.ROUNDED
                )
                self.console.print(panel)
        else:
            print(f"\n🔍 Symbolicated Output:")
            print("-" * 50)
            
            if show_full or len(lines) <= max_lines:
                for i, line in enumerate(lines, 1):
                    if COLORAMA_AVAILABLE:
                        if '<unknown>' in line:
                            print(f"{Fore.RED}{i:4}: {line}{Style.RESET_ALL}")
                        elif '+' in line and any(func in line for func in ['_', 'kernel', 'IOKit']):
                            print(f"{Fore.GREEN}{i:4}: {line}{Style.RESET_ALL}")
                        else:
                            print(f"{i:4}: {line}")
                    else:
                        print(f"{i:4}: {line}")
            else:
                for i, line in enumerate(lines[:max_lines], 1):
                    print(f"{i:4}: {line}")
                print(f"\n... ({len(lines) - max_lines} more lines)")
                print("Use --full flag to see complete output")
    
    def print_summary(self, result, processing_time=None):
        """Print final summary"""
        if RICH_AVAILABLE:
            status_style = "bold green" if result.get('success') else "bold red"
            status_icon = "✅" if result.get('success') else "❌"
            
            summary_text = f"{status_icon} {result.get('message', 'Processing completed')}"
            
            if processing_time:
                summary_text += f"\n⏱️  Processing time: {processing_time:.2f} seconds"
            
            if result.get('analysis_id'):
                summary_text += f"\n🆔 Analysis ID: {result['analysis_id']}"
            
            panel = Panel(
                Align.center(summary_text),
                title="📋 Summary",
                style=status_style,
                box=box.DOUBLE
            )
            self.console.print(panel)
        else:
            status_icon = "✅" if result.get('success') else "❌"
            message = result.get('message', 'Processing completed')
            
            if COLORAMA_AVAILABLE:
                color = Fore.GREEN if result.get('success') else Fore.RED
                print(f"\n{color}{Style.BRIGHT}📋 Summary:{Style.RESET_ALL}")
                print(f"{color}{status_icon} {message}{Style.RESET_ALL}")
            else:
                print(f"\n📋 Summary:")
                print(f"{status_icon} {message}")
            
            if processing_time:
                print(f"⏱️  Processing time: {processing_time:.2f} seconds")
            
            if result.get('analysis_id'):
                print(f"🆔 Analysis ID: {result['analysis_id']}")


def validate_file(filepath):
    """Validate the input file"""
    path = Path(filepath)
    
    if not path.exists():
        return False, f"File not found: {filepath}"
    
    if not path.is_file():
        return False, f"Path is not a file: {filepath}"
    
    allowed_extensions = {'.ips', '.crash', '.txt', '.json', '.log', '.panic'}
    if path.suffix.lower() not in allowed_extensions:
        return False, f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
    
    # Check file size (max 50MB)
    size = path.stat().st_size
    if size > 50 * 1024 * 1024:
        return False, f"File too large. Maximum size: 50MB, current: {size:,} bytes"
    
    if size == 0:
        return False, "File is empty"
    
    return True, None


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
        formatter.print_file_info(path.name, file_size)
        
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
        formatter.print_error("Make sure the IPSW Symbol Server is running")
        return None
    except requests.exceptions.Timeout:
        formatter.print_error("Request timeout - file processing took too long")
        return None
    except Exception as e:
        formatter.print_error(f"Unexpected error: {str(e)}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="🚀 IPSW Symbol Server CLI - Professional iOS Crash Symbolication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s crash.ips                           # Symbolicate local file
  %(prog)s crash.ips --server http://my-server:8000  # Custom server
  %(prog)s crash.ips --full                    # Show complete output
  %(prog)s crash.ips --save result.json        # Save result to file

Supported file types: .ips, .crash, .txt, .json, .log, .panic
"""
    )
    
    parser.add_argument('file', help='IPS/crash file to symbolicate')
    parser.add_argument('--server', '-s', 
                       default='http://localhost:8000',
                       help='IPSW Symbol Server URL (default: http://localhost:8000)')
    parser.add_argument('--full', '-f', action='store_true',
                       help='Show complete symbolicated output')
    parser.add_argument('--save', '-o', 
                       help='Save result to JSON file')
    parser.add_argument('--no-banner', action='store_true',
                       help='Skip banner display')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimal output mode')
    
    args = parser.parse_args()
    
    # Initialize formatter
    formatter = IPSWCLIFormatter()
    
    # Show banner
    if not args.no_banner and not args.quiet:
        formatter.print_banner()
    
    # Send request
    result_data = send_symbolication_request(args.server, args.file, formatter)
    
    if result_data is None:
        sys.exit(1)
    
    result, processing_time = result_data
    
    if not args.quiet:
        # Show device info
        if result.get('file_info'):
            formatter.print_device_info(result['file_info'])
        
        # Show symbolication stats
        if result.get('symbolicated_output'):
            formatter.print_symbolication_stats(result['symbolicated_output'])
        
        # Show output
        if result.get('symbolicated_output'):
            formatter.print_symbolicated_output(result['symbolicated_output'], args.full)
        
        # Show summary
        formatter.print_summary(result, processing_time)
    
    # Save to file if requested
    if args.save:
        try:
            with open(args.save, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            formatter.print_success(f"Result saved to: {args.save}")
        except Exception as e:
            formatter.print_error(f"Failed to save result: {e}")
    
    # Exit with appropriate code
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main() 