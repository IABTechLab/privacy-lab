"""
GCS Storage utility module for encrypted file storage.
Handles file encryption, upload to GCS, and file listing.
"""
import os
import base64
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
from google.cloud import storage
from google.cloud import secretmanager
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import io

# Load environment variables from .env file if it exists
load_dotenv()


class GCSStorage:
    """Handles encrypted file storage in GCS."""
    
    def __init__(self):
        """Initialize GCS storage client and encryption key."""
        # Get bucket name from environment
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME environment variable is required")
        
        # Initialize GCS client (Cloud Functions automatically provide credentials)
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(self.bucket_name)
        
        # Get encryption key
        self.encryption_key = self._get_encryption_key()
    
    def _get_encryption_key(self) -> bytes:
        """
        Get encryption key from Secret Manager or environment variable.
        
        Returns:
            bytes: AES-256 encryption key (32 bytes)
        """
        # Try Secret Manager first (production)
        project_id = os.getenv("GCP_PROJECT_ID")
        if project_id:
            try:
                secret_name = "encryption-key"
                client = secretmanager.SecretManagerServiceClient()
                name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                key_str = response.payload.data.decode("UTF-8")
                return base64.b64decode(key_str)
            except Exception as e:
                print(f"[WARN] Failed to fetch encryption key from Secret Manager: {e}")
        
        # Fallback to environment variable (local dev)
        key_str = os.getenv("ENCRYPTION_KEY")
        if not key_str:
            raise ValueError(
                "ENCRYPTION_KEY environment variable is required "
                "(or set GCP_PROJECT_ID to use Secret Manager)"
            )
        
        try:
            return base64.b64decode(key_str)
        except Exception:
            # If not base64, treat as raw key and pad/truncate to 32 bytes
            key_bytes = key_str.encode("utf-8")
            if len(key_bytes) < 32:
                # Pad with zeros
                key_bytes = key_bytes + b"\0" * (32 - len(key_bytes))
            elif len(key_bytes) > 32:
                # Truncate
                key_bytes = key_bytes[:32]
            return key_bytes
    
    def encrypt_file(self, file_content: bytes) -> bytes:
        """
        Encrypt file content using AES-256-GCM.
        
        Args:
            file_content: Raw file content to encrypt
            
        Returns:
            bytes: Encrypted file content
        """
        # Generate a random nonce (12 bytes for GCM)
        nonce = os.urandom(12)
        
        # Encrypt using AESGCM
        aesgcm = AESGCM(self.encryption_key)
        ciphertext = aesgcm.encrypt(nonce, file_content, None)
        
        # Prepend nonce to ciphertext (nonce + ciphertext)
        return nonce + ciphertext
    
    def upload_file(
        self, 
        user_id: str, 
        file_content: bytes, 
        file_type: str,
        original_filename: Optional[str] = None
    ) -> str:
        """
        Encrypt and upload file to GCS.
        
        Args:
            user_id: User ID from JWT token
            file_content: Raw file content
            file_type: Type of file ('events' or 'conversions')
            original_filename: Original filename (optional)
            
        Returns:
            str: GCS object path
        """
        # Encrypt file
        encrypted_content = self.encrypt_file(file_content)
        
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        if original_filename:
            # Extract extension from original filename
            ext = os.path.splitext(original_filename)[1] or ".csv"
            filename = f"{file_type}_{timestamp}{ext}"
        else:
            filename = f"{file_type}_{timestamp}.csv"
        
        # GCS object path: {userId}/{filename}
        blob_path = f"{user_id}/{filename}"
        
        # Upload to GCS
        blob = self.bucket.blob(blob_path)
        blob.upload_from_string(encrypted_content, content_type="application/octet-stream")
        
        print(f"[INFO] Uploaded encrypted file to GCS: {blob_path}")
        return blob_path
    
    def list_user_files(self, user_id: str) -> List[Dict[str, str]]:
        """
        List all files stored for a user.
        
        Args:
            user_id: User ID from JWT token
            
        Returns:
            List of file metadata dictionaries with keys:
            - path: GCS object path
            - filename: Filename
            - file_type: 'events' or 'conversions'
            - timestamp: Upload timestamp
        """
        # List all blobs with prefix {userId}/
        prefix = f"{user_id}/"
        blobs = self.storage_client.list_blobs(self.bucket_name, prefix=prefix)
        
        files = []
        for blob in blobs:
            # Extract filename from path
            filename = blob.name.split("/")[-1]
            
            # Parse file type and timestamp from filename
            # Format: {file_type}_{timestamp}.csv
            file_type = "unknown"
            timestamp = None
            
            if filename.startswith("events_"):
                file_type = "events"
            elif filename.startswith("conversions_"):
                file_type = "conversions"
            
            # Try to extract timestamp from filename
            try:
                # Format: events_20240101_120000.csv
                parts = filename.replace(".csv", "").split("_")
                if len(parts) >= 3:
                    timestamp = f"{parts[1]}_{parts[2]}"
            except Exception:
                pass
            
            files.append({
                "path": blob.name,
                "filename": filename,
                "file_type": file_type,
                "timestamp": timestamp or blob.time_created.isoformat() if blob.time_created else None,
                "size": blob.size
            })
        
        # Sort by timestamp (newest first)
        files.sort(key=lambda x: x["timestamp"] or "", reverse=True)
        
        return files
