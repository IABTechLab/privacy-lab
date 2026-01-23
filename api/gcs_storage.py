"""
GCS Storage utility module for file storage.
Handles file upload to GCS and file listing.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from google.cloud import storage
import io

# Load environment variables from .env file if it exists
load_dotenv()


class GCSStorage:
    """Handles file storage in GCS."""
    
    def __init__(self):
        """Initialize GCS storage client."""
        # Get bucket name from environment
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME environment variable is required")
        
        # File expiry time in hours (files older than this will be auto-deleted)
        self.file_expiry_hours = 1
        print(f"[INFO] GCS file expiry set to {self.file_expiry_hours} hour(s)")
        
        # Initialize GCS client (Cloud Functions automatically provide credentials)
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(self.bucket_name)
    
    def upload_file(
        self, 
        user_id: str, 
        file_content: bytes, 
        file_type: str,
        original_filename: Optional[str] = None
    ) -> str:
        """
        Upload file to GCS.
        
        Args:
            user_id: User ID from JWT token
            file_content: Raw file content
            file_type: Type of file ('events' or 'conversions')
            original_filename: Original filename (optional, not used)
            
        Returns:
            str: GCS object path
        """
        # Fixed filename structure: {user_id}/events.csv or {user_id}/conversions.csv
        # No timestamp - always overwrite the existing file
        filename = f"{file_type}.csv"
        
        # GCS object path: {userId}/{filename}
        blob_path = f"{user_id}/{filename}"
        
        # Upload to GCS
        blob = self.bucket.blob(blob_path)
        blob.upload_from_string(file_content, content_type="text/csv")
        
        print(f"[INFO] Uploaded file to GCS: {blob_path}")
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
            - uploaded_at: Upload timestamp (ISO format)
            - size: File size in bytes
        """
        # List all blobs with prefix {userId}/
        prefix = f"{user_id}/"
        blobs = self.storage_client.list_blobs(self.bucket_name, prefix=prefix)
        
        files = []
        for blob in blobs:
            # Extract filename from path
            filename = blob.name.split("/")[-1]
            
            # Parse file type from filename
            # Format: events.csv or conversions.csv
            file_type = "unknown"
            
            if filename == "events.csv":
                file_type = "events"
            elif filename == "conversions.csv":
                file_type = "conversions"
            
            files.append({
                "path": blob.name,
                "filename": filename,
                "file_type": file_type,
                "uploaded_at": blob.time_created.isoformat() if blob.time_created else None,
                "size": blob.size
            })
        
        # Sort by file_type for consistent ordering
        files.sort(key=lambda x: x["file_type"])
        
        return files
    
    def delete_file(self, user_id: str, file_type: str) -> bool:
        """
        Delete a file from GCS.
        
        Args:
            user_id: User ID from JWT token
            file_type: Type of file ('events' or 'conversions')
            
        Returns:
            bool: True if file was deleted, False if it didn't exist
        """
        blob_path = f"{user_id}/{file_type}.csv"
        blob = self.bucket.blob(blob_path)
        
        if blob.exists():
            blob.delete()
            print(f"[INFO] Deleted expired file from GCS: {blob_path}")
            return True
        
        return False
    
    def _is_file_expired(self, blob) -> bool:
        """
        Check if a file has expired based on its creation time.
        
        Args:
            blob: GCS blob object
            
        Returns:
            bool: True if file is expired, False otherwise
        """
        if not blob.time_created:
            return False
        
        # Get current time in UTC
        current_time = datetime.now(timezone.utc)
        
        # Ensure blob.time_created is timezone-aware
        file_time = blob.time_created
        if file_time.tzinfo is None:
            file_time = file_time.replace(tzinfo=timezone.utc)
        
        # Calculate time difference
        time_diff = current_time - file_time
        expiry_threshold = timedelta(hours=self.file_expiry_hours)
        
        return time_diff > expiry_threshold
    
    def check_files_exist(self, user_id: str, delete_expired: bool = False) -> Dict[str, bool]:
        """
        Check if events.csv and conversions.csv exist for a user and are not expired.
        
        Args:
            user_id: User ID from JWT token
            delete_expired: If True, delete expired files automatically
            
        Returns:
            Dict with keys 'events' and 'conversions' indicating existence and validity:
            - True: file exists and is not expired
            - False: file doesn't exist or is expired
        """
        result = {
            "events": False,
            "conversions": False
        }
        
        for file_type in ["events", "conversions"]:
            blob = self.bucket.blob(f"{user_id}/{file_type}.csv")
            
            if blob.exists():
                # Reload blob to get metadata
                blob.reload()
                
                # Check if file is expired
                if self._is_file_expired(blob):
                    print(f"[INFO] File {blob.name} is expired (created: {blob.time_created})")
                    if delete_expired:
                        self.delete_file(user_id, file_type)
                    result[file_type] = False
                else:
                    result[file_type] = True
            else:
                result[file_type] = False
        
        return result
    
    def download_file(self, user_id: str, file_type: str) -> Optional[bytes]:
        """
        Download a file from GCS.
        
        Args:
            user_id: User ID from JWT token
            file_type: Type of file ('events' or 'conversions')
            
        Returns:
            bytes: File content, or None if file doesn't exist
        """
        blob_path = f"{user_id}/{file_type}.csv"
        blob = self.bucket.blob(blob_path)
        
        if not blob.exists():
            print(f"[WARN] File not found in GCS: {blob_path}")
            return None
        
        print(f"[INFO] Downloading file from GCS: {blob_path}")
        return blob.download_as_bytes()
    
    def get_files_as_uploadfile(self, user_id: str) -> Dict[str, Optional[io.BytesIO]]:
        """
        Get events and conversions files as BytesIO objects suitable for parsing.
        
        Args:
            user_id: User ID from JWT token
            
        Returns:
            Dict with keys 'events' and 'conversions' containing BytesIO objects or None
        """
        result = {
            "events": None,
            "conversions": None
        }
        
        for file_type in ["events", "conversions"]:
            content = self.download_file(user_id, file_type)
            if content:
                result[file_type] = io.BytesIO(content)
        
        return result
