# 🚀 IPSW Symbol Server CLI Tool

Beautiful terminal interface for professional iOS crash symbolication. Send IPS files to your IPSW Symbol Server and get beautifully formatted results directly in your terminal.

## ✨ Features

- 🎨 **Beautiful Terminal Output** - Rich formatting with colors, tables, and progress indicators
- 📊 **Detailed Statistics** - Symbol counts, success rates, and quality indicators  
- 🔍 **Syntax Highlighting** - Code output with line numbers and color coding
- 📱 **Device Information** - Automatic extraction of device model, iOS version, and crash details
- 💾 **Export Options** - Save results to JSON files for later analysis
- ⚡ **Fast & Reliable** - Optimized for quick processing with proper error handling
- 🛠️ **Cross-Platform** - Works on macOS, Linux, and Windows

## 📦 Installation

### Quick Installation
```bash
curl -sSL https://github.com/mosiko1234/ipsw-auto-symbolicate-server/raw/main/install_cli.sh | bash
```

### Manual Installation

1. **Download the CLI script:**
   ```bash
   wget https://github.com/mosiko1234/ipsw-auto-symbolicate-server/raw/main/ipsw_cli.py
   chmod +x ipsw_cli.py
   ```

2. **Install dependencies:**
   ```bash
   pip3 install --user requests rich colorama
   ```

3. **Move to PATH (optional):**
   ```bash
   mv ipsw_cli.py ~/.local/bin/ipsw-cli
   export PATH="$HOME/.local/bin:$PATH"
   ```

## 🎯 Usage Examples

### Basic Usage
```bash
# Symbolicate a crash file
ipsw-cli crash.ips

# Use custom server
ipsw-cli crash.ips --server http://my-server:8000

# Show complete output (not truncated)
ipsw-cli crash.ips --full
```

### Advanced Usage
```bash
# Save results to JSON file
ipsw-cli crash.ips --save results.json

# Quiet mode (minimal output)
ipsw-cli crash.ips --quiet

# Skip banner
ipsw-cli crash.ips --no-banner

# Get help
ipsw-cli --help
```

## 📊 Sample Output

When you run the CLI tool, you'll see beautiful formatted output like this:

```
╔═══════════════════════════════════════════════════════════════╗
║                  🚀 IPSW Symbol Server CLI                   ║
║              Professional iOS Crash Symbolication            ║
╚═══════════════════════════════════════════════════════════════╝

📁 File Information
┌──────────┬─────────────────────┐
│ Property │ Value               │
├──────────┼─────────────────────┤
│ Filename │ crash.ips           │
│ Size     │ 45,231 bytes        │
│ Status   │ ✅ Ready for upload │
└──────────┴─────────────────────┘

✅ File processed successfully!

📱 Device & Crash Information
┌─────────────┬──────────────────┐
│ Property    │ Value            │
├─────────────┼──────────────────┤
│ Device      │ iPhone 15 Pro    │
│ iOS Version │ 18.5             │
│ Build       │ 22F76            │
│ Process     │ MyApp            │
│ Bug Type    │ 309              │
│ File Type   │ IPS Format       │
└─────────────┴──────────────────┘

📊 Symbolication Statistics
┌─────────────────┬───────┬───────────┐
│ Metric          │ Count │ Status    │
├─────────────────┼───────┼───────────┤
│ Symbols Found   │   245 │ ✅        │
│ Unknown Symbols │    12 │ ❓        │
│ Kernel Addresses│     3 │ 🔧        │
│ Success Rate    │ 95.3% │ Excellent │
└─────────────────┴───────┴───────────┘
```

## 🔧 Options

| Option | Short | Description |
|--------|-------|-------------|
| `--server` | `-s` | IPSW Symbol Server URL (default: http://localhost:8000) |
| `--full` | `-f` | Show complete symbolicated output (not truncated) |
| `--save` | `-o` | Save result to JSON file |
| `--quiet` | `-q` | Minimal output mode |
| `--no-banner` | | Skip banner display |
| `--help` | `-h` | Show help message |

## 📂 Supported File Types

- `.ips` - iOS Panic/Stackshot files (preferred)
- `.crash` - Crash logs
- `.txt` - Text-based crash logs  
- `.json` - JSON formatted crash data
- `.log` - Generic log files
- `.panic` - Kernel panic files

## 🎨 Rich Output Features

### With Rich Library (Recommended)
When the `rich` library is installed, you get:
- ✨ Beautiful tables and panels
- 🌈 Syntax highlighting for crash logs
- 📊 Progress indicators with spinners
- 🎯 Color-coded error/success messages
- 📋 Formatted panels with borders

### Fallback Mode
Without `rich`, the tool gracefully falls back to:
- 🎨 Colorama-based coloring
- 📝 Simple text formatting
- ✅ All functionality preserved
- 🖥️ Cross-platform compatibility

## 🚨 Error Handling

The CLI tool provides clear error messages for common issues:

- **File not found** - Clear path information
- **Invalid file type** - List of supported formats
- **Server connection issues** - Network troubleshooting tips
- **Authentication errors** - Server configuration guidance
- **Processing timeouts** - Retry suggestions

## 🔄 Integration Examples

### CI/CD Pipeline
```bash
#!/bin/bash
# Automatic crash symbolication in CI

for crash_file in crashes/*.ips; do
    echo "Processing $crash_file..."
    ipsw-cli "$crash_file" --server https://symbol-server.company.com --save "${crash_file%.ips}.json"
done
```

### Batch Processing
```bash
#!/bin/bash
# Process multiple crash files

find . -name "*.ips" -exec ipsw-cli {} --quiet --save {}.json \;
```

### Development Workflow
```bash
# Quick symbolication during development
alias symbolicate='ipsw-cli --server http://dev-server:8000'

# Use it
symbolicate latest_crash.ips
```

## 🌐 Server Requirements

The CLI tool works with any IPSW Symbol Server that provides:
- POST `/symbolicate` endpoint
- File upload support
- JSON response format

Default server: `http://localhost:8000`

## 🆘 Troubleshooting

### Installation Issues
```bash
# Check Python version
python3 --version

# Install dependencies manually
pip3 install requests rich colorama

# Verify installation
ipsw-cli --help
```

### Connection Issues
```bash
# Test server connectivity
curl http://localhost:8000/health

# Check firewall settings
telnet localhost 8000
```

### Permission Issues
```bash
# Fix script permissions
chmod +x ipsw_cli.py

# Install to user directory
pip3 install --user package_name
```

## 📈 Performance Tips

- Use `--quiet` mode for scripting
- Process files locally when possible
- Use `--no-banner` in automated scripts
- Save results with `--save` for analysis

## 🤝 Contributing

Found a bug or want to contribute? 
- Report issues on GitHub
- Submit pull requests
- Share usage examples
- Improve documentation

## 📄 License

This CLI tool is part of the IPSW Symbol Server project.
Licensed under the MIT License.

---

**Made with ❤️ for iOS developers**

For more information, visit: https://github.com/mosiko1234/ipsw-auto-symbolicate-server 