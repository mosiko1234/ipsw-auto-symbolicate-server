import json
import logging
from pathlib import Path
import httpx
from datetime import datetime, timedelta
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeviceMappingManager:
    """
    Manages the mapping from device identifiers (e.g., iPhone17,3) to
    marketing names (e.g., iPhone 16) using data from appledb.dev.
    """
    
    # URL to the device list JSON file from the appledb.dev GitHub repo
    DB_URL = "https://raw.githubusercontent.com/littlebyteorg/appledb-data/main/dist/device-list.json"
    
    # Local cache settings
    CACHE_DIR = Path("/tmp/appledb_cache")
    CACHE_FILE = CACHE_DIR / "device-list.json"
    CACHE_EXPIRY = timedelta(days=7)  # Update the cache once a week

    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._device_map = None
        self._ensure_db_updated()

    def _is_cache_expired(self) -> bool:
        """Check if the local cache file is older than the expiry time."""
        if not self.CACHE_FILE.exists():
            return True
        
        file_mod_time = datetime.fromtimestamp(self.CACHE_FILE.stat().st_mtime)
        return (datetime.now() - file_mod_time) > self.CACHE_EXPIRY

    def _ensure_db_updated(self):
        """
        Ensures the device database is up-to-date by checking the cache
        and downloading a new version if necessary.
        """
        if self._is_cache_expired():
            logger.info("AppleDB device list cache is expired or missing. Downloading new version...")
            try:
                response = httpx.get(self.DB_URL, follow_redirects=True, timeout=30)
                response.raise_for_status()
                
                # Save the new data to the cache file
                with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                logger.info("Successfully downloaded and cached new device list from AppleDB.")
                self._device_map = json.loads(response.text)
            except httpx.RequestError as e:
                logger.error(f"Failed to download device list from {self.DB_URL}: {e}")
                # If download fails, try to use the old cache if it exists
                if self.CACHE_FILE.exists():
                    logger.warning("Using existing (but potentially outdated) cached device list.")
                    with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                        self._device_map = json.load(f)
                else:
                    self._device_map = {}  # No data available
        else:
            logger.info("Using cached AppleDB device list.")
            if not self._device_map:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    self._device_map = json.load(f)

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
            logger.error("Device map is not loaded. Cannot translate identifier.")
            return identifier  # Return original identifier as a fallback

        # The device list is a dictionary where keys are identifiers
        device_info = self._device_map.get(identifier)
        
        if device_info and 'name' in device_info:
            marketing_name = device_info['name']
            logger.info(f"Mapped '{identifier}' to '{marketing_name}'")
            return marketing_name
        
        logger.warning(f"Identifier '{identifier}' not found in AppleDB. Returning original identifier.")
        return identifier

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