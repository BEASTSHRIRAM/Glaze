"""Indexing service orchestration."""
import logging
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.drive_service import DriveService
from services.file_processor import FileProcessor
from services.embedding_service import EmbeddingService
from services.qdrant_service import QdrantService
from database import (
    get_file_metadata,
    insert_file_metadata,
    update_indexing_status,
    get_indexing_status,
    is_file_indexed
)

logger = logging.getLogger(__name__)


@dataclass
class IndexResult:
    """Result of indexing a single file."""
    file_id: str
    status: str  # 'success', 'skipped', 'failed'
    chunk_count: int
    error: Optional[str] = None


class IndexingService:
    """Orchestrates the file indexing pipeline."""
    
    def __init__(
        self,
        drive_service: DriveService,
        file_processor: FileProcessor,
        embedding_service: EmbeddingService,
        qdrant_service: QdrantService
    ):
        """
        Initialize indexing service.
        
        Args:
            drive_service: Google Drive service
            file_processor: File content processor
            embedding_service: Embedding generation service
            qdrant_service: Qdrant vector database service
        """
        self.drive_service = drive_service
        self.file_processor = file_processor
        self.embedding_service = embedding_service
        self.qdrant_service = qdrant_service
    
    def is_indexed(self, file_id: str) -> bool:
        """Check if file has been indexed."""
        return is_file_indexed(file_id)
    
    def should_reindex(self, file_id: str, modified_time: str) -> bool:
        """
        Check if file should be re-indexed based on modification time.
        
        Args:
            file_id: Google Drive file ID
            modified_time: Current modification time from Drive
            
        Returns:
            True if file should be re-indexed
        """
        metadata = get_file_metadata(file_id)
        if not metadata:
            return True
        
        stored_modified_time = metadata.get('modified_time')
        if not stored_modified_time:
            return True
        
        return modified_time != stored_modified_time
    
    def index_file(
        self,
        file_metadata: Dict[str, Any],
        force_reindex: bool = False
    ) -> IndexResult:
        """
        Index a single file through the complete pipeline.
        
        Args:
            file_metadata: File metadata from Google Drive
            force_reindex: Force re-indexing even if already indexed
            
        Returns:
            IndexResult with status and details
        """
        file_id = file_metadata['id']
        file_name = file_metadata['name']
        mime_type = file_metadata['mimeType']
        link = file_metadata.get('webViewLink', '')
        modified_time = file_metadata.get('modifiedTime', '')
        
        try:
            # Check if should skip
            if not force_reindex:
                if self.is_indexed(file_id) and not self.should_reindex(file_id, modified_time):
                    logger.info(f"Skipping already indexed file: {file_name}")
                    return IndexResult(
                        file_id=file_id,
                        status='skipped',
                        chunk_count=0
                    )
            
            # If re-indexing, delete old embeddings
            if self.is_indexed(file_id):
                logger.info(f"Re-indexing file: {file_name}")
                self.qdrant_service.delete_file_embeddings(file_id)
            
            # Download file content
            logger.info(f"Downloading file: {file_name}")
            file_content, actual_mime = self.drive_service.download_file(file_id, mime_type)
            
            # Use actual_mime for downstream processing
            logger.debug(f"File {file_name} downloaded as {actual_mime}")
            
            # Multimodal support
            if self.file_processor.is_multimodal(actual_mime):
                logger.info(f"Using multimodal embedding for: {file_name} ({actual_mime})")
                try:
                    # For PDF, we still prefer text extraction for better searchability if possible
                    if actual_mime != "application/pdf":
                        embedding = self.embedding_service.generate_multimodal_embedding(file_content, actual_mime)
                        # ... rest of logic
                        
                        chunk_data = [{
                            'chunk_id': str(uuid.uuid4()),
                            'file_id': file_id,
                            'file_name': file_name,
                            'chunk_text': f"Multimodal content: {file_name}",
                            'mime_type': mime_type,
                            'chunk_index': 0
                        }]
                        
                        self.qdrant_service.store_embeddings_batch(chunk_data, [embedding])
                        insert_file_metadata(file_id, file_name, mime_type, link, modified_time)
                        update_indexing_status(file_id, 'completed', 1)
                        
                        logger.info(f"Successfully indexed multimodal file: {file_name}")
                        return IndexResult(file_id=file_id, status='success', chunk_count=1)
                except Exception as e:
                    logger.warning(f"Native multimodal embedding failed, falling back to text: {str(e)}")

            # Extract text
            logger.info(f"Extracting text from: {file_name}")
            try:
                text = self.file_processor.extract_text(file_content, actual_mime)
            except Exception as e:
                logger.error(f"Text extraction failed for {file_name}: {str(e)}")
                update_indexing_status(file_id, 'failed', 0, f"Extraction failed: {str(e)}")
                return IndexResult(file_id=file_id, status='failed', chunk_count=0, error=str(e))
            
            if not text or not text.strip():
                logger.warning(f"No text extracted from file: {file_name}")
                update_indexing_status(file_id, 'failed', 0, "No text content")
                return IndexResult(file_id=file_id, status='failed', chunk_count=0, error="No text content")
            
            # Chunk text
            logger.info(f"Chunking text from: {file_name}")
            chunks = self.file_processor.chunk_text(text)
            
            if not chunks:
                logger.warning(f"No chunks created from file: {file_name}")
                update_indexing_status(file_id, 'failed', 0, "No chunks created")
                return IndexResult(file_id=file_id, status='failed', chunk_count=0, error="No chunks created")
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(chunks)} chunks from: {file_name}")
            embeddings = self.embedding_service.generate_embeddings_batch(chunks)
            
            # Prepare chunk metadata
            chunk_data = []
            for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_data.append({
                    'chunk_id': str(uuid.uuid4()),
                    'file_id': file_id,
                    'file_name': file_name,
                    'chunk_text': chunk_text,
                    'mime_type': mime_type,
                    'chunk_index': idx
                })
            
            # Store in Qdrant
            logger.info(f"Storing {len(chunk_data)} embeddings in Qdrant")
            self.qdrant_service.store_embeddings_batch(chunk_data, embeddings)
            
            # Store metadata in SQLite
            insert_file_metadata(file_id, file_name, mime_type, link, modified_time)
            update_indexing_status(file_id, 'completed', len(chunks))
            
            logger.info(f"Successfully indexed file: {file_name} ({len(chunks)} chunks)")
            return IndexResult(
                file_id=file_id,
                status='success',
                chunk_count=len(chunks)
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to index file {file_name}: {error_msg}")
            update_indexing_status(file_id, 'failed', 0, error_msg)
            return IndexResult(
                file_id=file_id,
                status='failed',
                chunk_count=0,
                error=error_msg
            )
    
    def index_files(
        self,
        files: List[Dict[str, Any]],
        force_reindex: bool = False,
        max_workers: int = 5
    ) -> Dict[str, Any]:
        """
        Index multiple files with parallel processing.
        
        Args:
            files: List of file metadata from Google Drive
            force_reindex: Force re-indexing
            max_workers: Maximum concurrent workers
            
        Returns:
            Summary dict with counts and errors
        """
        results = {
            'indexed_count': 0,
            'skipped_count': 0,
            'failed_count': 0,
            'errors': []
        }
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.index_file, file_meta, force_reindex): file_meta
                for file_meta in files
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    
                    if result.status == 'success':
                        results['indexed_count'] += 1
                    elif result.status == 'skipped':
                        results['skipped_count'] += 1
                    elif result.status == 'failed':
                        results['failed_count'] += 1
                        results['errors'].append({
                            'file_id': result.file_id,
                            'error': result.error
                        })
                        
                except Exception as e:
                    logger.error(f"Unexpected error in indexing: {str(e)}")
                    results['failed_count'] += 1
        
        logger.info(
            f"Indexing complete: {results['indexed_count']} indexed, "
            f"{results['skipped_count']} skipped, {results['failed_count']} failed"
        )
        
        return results
