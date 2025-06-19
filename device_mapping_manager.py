import json
import logging
from pathlib import Path
import httpx
from datetime import datetime, timedelta
from typing import Optional
import subprocess
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeviceMappingManager:
    """
    Manages the mapping from device identifiers (e.g., iPhone17,3) to
    marketing names (e.g., iPhone 16) using data from appledb.dev.
    
    Works in offline mode by checking for local git repository first.
    """
    
    # URLs and repository information
    API_BASE_URL = "https://api.appledb.dev"
    DB_URL = f"{API_BASE_URL}/device/{{identifier}}.json"  # Device-specific endpoint
    GIT_REPO_URL = "https://github.com/littlebyteorg/appledb.git"
    
    # Local paths
    LOCAL_REPO_DIR = Path("./data/appledb")  # Local git repository
    CACHE_DIR = Path("/tmp/appledb_cache")
    CACHE_FILE = CACHE_DIR / "device-list.json"
    CACHE_EXPIRY = timedelta(days=7)  # Update the cache once a week

    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.LOCAL_REPO_DIR.parent.mkdir(parents=True, exist_ok=True)
        self._device_map = None
        self._ensure_db_updated()

    def _is_cache_expired(self) -> bool:
        """Check if the local cache file is older than the expiry time."""
        if not self.CACHE_FILE.exists():
            return True
        
        file_mod_time = datetime.fromtimestamp(self.CACHE_FILE.stat().st_mtime)
        return (datetime.now() - file_mod_time) > self.CACHE_EXPIRY

    def _load_from_local_git(self) -> bool:
        # AIRGAP: Only load from local AppleDB, never try to update/clone/pull
        device_dirs = [
            self.LOCAL_REPO_DIR / "deviceFiles" / "iPhone",
            self.LOCAL_REPO_DIR / "deviceFiles" / "iPad",
            self.LOCAL_REPO_DIR / "deviceFiles" / "iPod touch",
            self.LOCAL_REPO_DIR / "deviceFiles" / "Apple TV",
            self.LOCAL_REPO_DIR / "deviceFiles" / "Apple Watch",
            self.LOCAL_REPO_DIR / "deviceFiles" / "HomePod",
        ]
        device_map = {}
        total_devices = 0
        for device_dir in device_dirs:
            if not device_dir.exists():
                continue
            try:
                logger.info(f"Loading devices from: {device_dir}")
                for device_file in device_dir.glob("*.json"):
                    try:
                        with open(device_file, 'r', encoding='utf-8') as f:
                            device_data = json.load(f)
                        if "identifier" in device_data and "name" in device_data:
                            identifier = device_data["identifier"]
                            device_map[identifier] = {
                                "name": device_data["name"],
                                "type": device_data.get("type", "Unknown"),
                                "released": device_data.get("released", "Unknown"),
                                "soc": device_data.get("soc", "Unknown")
                            }
                            total_devices += 1
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Skipping invalid device file {device_file}: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Error loading devices from {device_dir}: {e}")
                continue
        if device_map:
            self._device_map = device_map
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._device_map, f, ensure_ascii=False, indent=2)
            logger.info(f"Successfully loaded {total_devices} devices from local AppleDB.")
            return True
        else:
            logger.error("No valid device data found in local AppleDB. Airgap mode requires local copy.")
            return False

    def _clone_or_update_git_repo(self) -> bool:
        # AIRGAP: Disabled. Never clone or update from internet.
        logger.error("[AIRGAP] Attempted to update AppleDB from internet. This is disabled in airgap mode.")
        return False

    def _download_via_http(self, identifier: str) -> Optional[dict]:
        # AIRGAP: Disabled. Never download from internet.
        logger.error(f"[AIRGAP] Attempted to download device info for {identifier} from internet. This is disabled in airgap mode.")
        return None

    def _ensure_db_updated(self):
        # AIRGAP: Only load from local AppleDB, never update/clone/pull
        if self._load_from_local_git():
            return
        if self.CACHE_FILE.exists():
            logger.warning("Using existing (but potentially outdated) cached device list.")
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    self._device_map = json.load(f)
            except (json.JSONDecodeError, IOError):
                logger.error("Failed to load cache file. Using empty device map.")
                self._device_map = {}
        else:
            logger.error("No local AppleDB or cache available. Airgap mode requires local copy.")
            self._device_map = {}

    def get_marketing_name(self, identifier: str) -> Optional[str]:
        """
        Translates a device identifier to its marketing name.
        
        Args:
            identifier: The device identifier (e.g., "iPhone17,3").
            
        Returns:
            The marketing name (e.g., "iPhone 16") or the original identifier
            if no mapping is found.
        """
        if not self._device_map:
            self._device_map = {}

        # Check if we already have this device in our map
        if identifier in self._device_map:
            device_info = self._device_map[identifier]
            marketing_name = device_info['name']
            logger.info(f"Mapped '{identifier}' to '{marketing_name}' (cached)")
            return marketing_name
        
        # Try to fetch device info online if not in cache
        logger.info(f"Device '{identifier}' not found in cache, trying to fetch online...")
        device_data = self._download_via_http(identifier)
        
        if device_data:
            # Add to cache
            self._device_map[identifier] = device_data
            
            # Update cache file
            try:
                with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self._device_map, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning(f"Failed to update cache file: {e}")
            
            marketing_name = device_data['name']
            logger.info(f"Mapped '{identifier}' to '{marketing_name}' (online)")
            return marketing_name
        
        logger.warning(f"Identifier '{identifier}' not found in AppleDB. Returning original identifier.")
        return identifier
    
    def get_device_identifier(self, marketing_name: str) -> Optional[str]:
        """
        Reverse lookup: translates a marketing name to device identifier.
        
        Args:
            marketing_name: The marketing name (e.g., "iPhone 14 Pro").
            
        Returns:
            The device identifier (e.g., "iPhone15,2") or None if no mapping is found.
        """
        if not self._device_map:
            logger.warning("Device map not loaded")
            return None
        
        # Normalize the marketing name for comparison (case-insensitive, strip spaces)
        normalized_marketing = marketing_name.strip().lower()
        
        # Search through all devices for a matching marketing name
        for identifier, device_info in self._device_map.items():
            device_name = device_info.get('name', '').strip().lower()
            if device_name == normalized_marketing:
                logger.info(f"Reverse mapped '{marketing_name}' to '{identifier}'")
                return identifier
        
        # Try fuzzy matching for common variations
        for identifier, device_info in self._device_map.items():
            device_name = device_info.get('name', '').strip().lower()
            # Handle variations like "iPhone 14 Pro" vs "iPhone14,2"
            if 'iphone' in normalized_marketing and 'iphone' in device_name:
                # Remove non-alphanumeric for fuzzy comparison
                normalized_clean = ''.join(c for c in normalized_marketing if c.isalnum())
                device_clean = ''.join(c for c in device_name if c.isalnum())
                if normalized_clean == device_clean:
                    logger.info(f"Reverse mapped '{marketing_name}' to '{identifier}' (fuzzy match)")
                    return identifier
        
        logger.warning(f"Marketing name '{marketing_name}' not found in device mapping.")
        return None

# Example usage:
if __name__ == '__main__':
    mapper = DeviceMappingManager()
    
    # Test with a known identifier
    identifier_known = "iPhone15,2"
    name_known = mapper.get_marketing_name(identifier_known)
    print(f"'{identifier_known}' is mapped to: '{name_known}'")
    
    # Test with a hypothetical future identifier
    identifier_future = "iPhone17,3"
    name_future = mapper.get_marketing_name(identifier_future)
    print(f"'{identifier_future}' is mapped to: '{name_future}'")

    # Test with a non-existent identifier
    identifier_fake = "FakeDevice1,1"
    name_fake = mapper.get_marketing_name(identifier_fake)
    print(f"'{identifier_fake}' is mapped to: '{name_fake}'") 