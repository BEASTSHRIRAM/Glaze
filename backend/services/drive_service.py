"""Google Drive service for file retrieval."""
import logging
import io
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

# Supported MIME types
SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.google-apps.document",
    "text/plain",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    # Images
    "image/png", "image/jpeg", "image/jpg", "image/webp", "image/heic", "image/heif",
    # Video
    "video/mp4", "video/mov", "video/quicktime",
    # Audio
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/aac"
}

# Export MIME types for Google Docs
EXPORT_MIME_TYPES = {
    "application/vnd.google-apps.document": "application/pdf",
    "application/vnd.google-apps.spreadsheet": "application/pdf",
    "application/vnd.google-apps.presentation": "application/pdf"
}


class DriveService:
    """Service for interacting with Google Drive API."""
    
    def __init__(self, credentials: Credentials):
        """
        Initialize Drive service with credentials.
        
        Args:
            credentials: Google OAuth2 credentials
        """
        self.service = build('drive', 'v3', credentials=credentials)
        logger.info("Drive service initialized")
    
    def list_files(self, page_token: Optional[str] = None) -> Dict[str, Any]:
        """
        List files from Google Drive with pagination.
        
        Args:
            page_token: Token for pagination (optional)
            
        Returns:
            Dict containing 'files' list and 'nextPageToken'
        """
        try:
            # Build query for supported file types
            mime_type_query = " or ".join([
                f"mimeType='{mime}'" for mime in SUPPORTED_MIME_TYPES
            ])
            
            # Add Google Docs types
            for google_mime in EXPORT_MIME_TYPES.keys():
                mime_type_query += f" or mimeType='{google_mime}'"
            
            query = f"({mime_type_query}) and trashed=false"
            
            results = self.service.files().list(
                q=query,
                pageSize=100,
                pageToken=page_token,
                fields="nextPageToken, files(id, name, mimeType, webViewLink, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            next_page_token = results.get('nextPageToken')
            
            logger.info(f"Retrieved {len(files)} files from Drive")
            
            return {
                "files": files,
                "nextPageToken": next_page_token
            }
            
        except Exception as e:
            logger.error(f"Failed to list Drive files: {str(e)}")
            raise Exception(f"Drive API error: {str(e)}")
    
    def list_all_files(self) -> List[Dict[str, Any]]:
        """
        List all files from Google Drive, handling pagination automatically.
        
        Returns:
            List of all files
        """
        all_files = []
        page_token = None
        
        while True:
            result = self.list_files(page_token=page_token)
            all_files.extend(result['files'])
            
            page_token = result.get('nextPageToken')
            if not page_token:
                break
        
        logger.info(f"Retrieved total of {len(all_files)} files from Drive")
        return all_files
    
    def download_file(self, file_id: str, mime_type: str) -> tuple[bytes, str]:
        """
        Download file content from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            mime_type: MIME type of the file
            
        Returns:
            File content as bytes
        """
        try:
            # Check if it's a Google Docs file that needs export
            if mime_type in EXPORT_MIME_TYPES:
                export_mime = EXPORT_MIME_TYPES[mime_type]
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType=export_mime
                )
                logger.info(f"Exporting Google Doc {file_id} as {export_mime}")
            else:
                request = self.service.files().get_media(fileId=file_id)
                logger.info(f"Downloading file {file_id}")
            
            file_buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(file_buffer, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download progress: {int(status.progress() * 100)}%")
            
            content = file_buffer.getvalue()
            logger.info(f"Downloaded {len(content)} bytes for file {file_id}")
            actual_mime = EXPORT_MIME_TYPES.get(mime_type, mime_type)
            return content, actual_mime
            
        except Exception as e:
            logger.error(f"Failed to download file {file_id}: {str(e)}")
            raise Exception(f"Failed to download file: {str(e)}")
    
    def filter_supported_files(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter files to only include supported MIME types.
        
        Args:
            files: List of file metadata dicts
            
        Returns:
            Filtered list of files
        """
        supported_files = [
            f for f in files 
            if f.get('mimeType') in SUPPORTED_MIME_TYPES or 
               f.get('mimeType') in EXPORT_MIME_TYPES
        ]
        
        logger.info(f"Filtered {len(supported_files)} supported files from {len(files)} total")
        return supported_files
