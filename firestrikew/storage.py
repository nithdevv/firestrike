import os
import json
import logging
from typing import Dict, Tuple, Optional
from pathlib import Path

class Storage:
    def __init__(self, storage_dir: str = None):
        if storage_dir is None:
            # Use Downloads folder as default
            self.storage_dir = Path.home() / "Downloads" / "firestrike_data"
        else:
            self.storage_dir = Path(storage_dir)
            
        self.data_dir = self.storage_dir / "data"
        self.metadata_file = self.storage_dir / "metadata.json"
        self.metadata: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
        
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load metadata if exists
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load metadata: {e}")
                self.metadata = {}
                
    def store_data(self, data_hash: str, data: bytes, salt: bytes) -> None:
        """Store data and its metadata"""
        try:
            # Save data to file
            data_path = self.data_dir / data_hash
            with open(data_path, 'wb') as f:
                f.write(data)
            
            # Update metadata
            self.metadata[data_hash] = {
                'size': len(data),
                'salt': salt.hex()
            }
            
            # Save metadata
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f)
                
        except Exception as e:
            self.logger.error(f"Failed to store data {data_hash}: {e}")
            raise
            
    def get_data(self, data_hash: str) -> Optional[Tuple[bytes, bytes]]:
        """Retrieve data and its salt by hash"""
        try:
            if data_hash not in self.metadata:
                return None
                
            data_path = self.data_dir / data_hash
            if not data_path.exists():
                return None
                
            # Read data
            with open(data_path, 'rb') as f:
                data = f.read()
                
            # Get salt from metadata
            salt = bytes.fromhex(self.metadata[data_hash]['salt'])
            
            return data, salt
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve data {data_hash}: {e}")
            return None
            
    def list_files(self) -> Dict[str, Dict]:
        """Return list of stored files"""
        return self.metadata.copy()
        
    def remove_data(self, data_hash: str) -> bool:
        """Remove data and its metadata"""
        try:
            if data_hash not in self.metadata:
                return False
                
            # Remove data file
            data_path = self.data_dir / data_hash
            if data_path.exists():
                os.unlink(data_path)
                
            # Remove from metadata
            del self.metadata[data_hash]
            
            # Save metadata
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove data {data_hash}: {e}")
            return False 