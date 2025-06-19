#!/usr/bin/env python3
"""
IPSW Symbol Server - Kernel Symbolication Setup Checker
Checks if the kernel symbolication daemon is properly configured.
"""

import os
import sys
import yaml
import psycopg2
from pathlib import Path

def check_config_file():
    """Check if the IPSW config file exists and is properly configured."""
    config_path = Path.home() / ".config" / "ipsw" / "config.yml"
    
    print(f"🔍 Checking config file: {config_path}")
    
    if not config_path.exists():
        print("❌ Config file not found!")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check database config
        if 'database' in config:
            db = config['database']
            print(f"✅ Database configured: {db.get('driver')}://{db.get('user')}@{db.get('host')}:{db.get('port')}/{db.get('name')}")
        else:
            print("❌ Database configuration missing")
            return False
        
        # Check daemon config
        if 'daemon' in config and 'sigs-dir' in config['daemon']:
            sigs_dir = config['daemon']['sigs-dir']
            print(f"✅ Kernel signatures directory: {sigs_dir}")
            
            if os.path.exists(sigs_dir):
                json_files = len(list(Path(sigs_dir).rglob("*.json")))
                print(f"✅ Found {json_files} signature files")
            else:
                print(f"❌ Signatures directory not found: {sigs_dir}")
                return False
        else:
            print("❌ Daemon configuration missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False

def check_database():
    """Check if the database has the required tables for kernel symbolication."""
    print("\n🔍 Checking database setup...")
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="symbols",
            user="symbols_user",
            password="symbols_password"
        )
        
        cursor = conn.cursor()
        
        # Check for kernel_symbols table
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'kernel_symbols'
            );
        """)
        
        if cursor.fetchone()[0]:
            print("✅ kernel_symbols table exists")
        else:
            print("❌ kernel_symbols table missing")
            return False
        
        # Check for daemon_config table
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'daemon_config'
            );
        """)
        
        if cursor.fetchone()[0]:
            print("✅ daemon_config table exists")
            
            # Show daemon configuration
            cursor.execute("SELECT config_key, config_value, description FROM daemon_config")
            configs = cursor.fetchall()
            
            print("📋 Daemon Configuration:")
            for key, value, desc in configs:
                print(f"   {key}: {value} ({desc})")
        else:
            print("❌ daemon_config table missing")
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def check_symbolicator_repo():
    """Check if the symbolicator repository is properly cloned (airgap: must be local)."""
    print("\n🔍 Checking symbolicator repository...")
    repo_path = Path("./data/symbolicator")
    kernel_path = repo_path / "kernel"
    if not repo_path.exists():
        print("❌ Symbolicator repository not found (airgap mode requires local copy)")
        return False
    if not kernel_path.exists():
        print("❌ Kernel signatures directory not found (airgap mode requires local copy)")
        return False
    json_files = list(kernel_path.rglob("*.json"))
    print(f"✅ Symbolicator repository found with {len(json_files)} signature files")
    ios_versions = set()
    for json_file in json_files[:50]:
        parts = str(json_file).split('/')
        for part in parts:
            if part.startswith(('20', '21', '22', '23', '24')):
                ios_versions.add(part)
    if ios_versions:
        print(f"📱 Available iOS versions: {sorted(ios_versions)}")
    return True

def main():
    """Main function to run all checks."""
    print("🔧 IPSW Symbol Server - Kernel Symbolication Setup Checker")
    print("=" * 60)
    checks = [
        ("Configuration File", check_config_file),
        ("Database Setup", check_database),
        ("Symbolicator Repository", check_symbolicator_repo)
    ]
    all_passed = True
    for check_name, check_func in checks:
        if not check_func():
            all_passed = False
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All checks passed! Kernel symbolication is ready to use.")
        print("\n📝 To use kernel symbolication:")
        print("   1. Upload an IPSW file containing kernel cache")
        print("   2. Process IPS files - they will be automatically symbolicated")
        print("   3. Check the database for symbolicated results")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\n🔧 Quick fixes:")
        print("   - Ensure ./data/symbolicator exists and contains all required signatures (airgap mode)")
        print("   - Ensure Docker containers are running")
        print("   - Check database credentials")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 