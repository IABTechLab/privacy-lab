"""
GCS Storage utility module for file storage.
Handles file upload to GCS and file listing.
"""
import os
from datetime import datetime
from typing import List, Dict, Optional
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
            original_filename: Original filename (optional)
            
        Returns:
            str: GCS object path
        """
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
