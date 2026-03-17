"""Qdrant vector database service."""
import logging
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from config import get_settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "drive_files"
VECTOR_SIZE = 768  # Gemini embedding dimension


class QdrantService:
    """Service for interacting with Qdrant vector database."""
    
    def __init__(self):
        """Initialize Qdrant client."""
        settings = get_settings()
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        logger.info(f"Qdrant client initialized: {settings.qdrant_host}:{settings.qdrant_port}")
    
    def initialize_collection(self) -> None:
        """Create collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if COLLECTION_NAME not in collection_names:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=VECTOR_SIZE,
                        distance=Distance.COSINE
                    ),
                    hnsw_config={
                        "m": 16,
                        "ef_construct": 100
                    }
                )
                logger.info(f"Created collection: {COLLECTION_NAME}")
            else:
                logger.info(f"Collection {COLLECTION_NAME} already exists")
                
        except Exception as e:
            logger.error(f"Failed to initialize collection: {str(e)}")
            raise
    
    def store_embedding(
        self,
        chunk_id: str,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> None:
        """
        Store embedding vector with metadata.
        
        Args:
            chunk_id: Unique identifier for the chunk
            vector: Embedding vector
            payload: Metadata (file_id, file_name, chunk_text, mime_type, chunk_index)
        """
        try:
            point = PointStruct(
                id=chunk_id,
                vector=vector,
                payload=payload
            )
            
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=[point]
            )
            
            logger.debug(f"Stored embedding for chunk: {chunk_id}")
            
        except Exception as e:
            logger.error(f"Failed to store embedding: {str(e)}")
            raise
    
    def store_embeddings_batch(
        self,
        chunks: List[Dict[str, Any]],
        vectors: List[List[float]]
    ) -> None:
        """
        Store multiple embeddings in batch.
        
        Args:
            chunks: List of chunk metadata dicts
            vectors: List of embedding vectors
        """
        try:
            points = []
            for chunk, vector in zip(chunks, vectors):
                chunk_id = chunk.get('chunk_id', str(uuid.uuid4()))
                point = PointStruct(
                    id=chunk_id,
                    vector=vector,
                    payload=chunk
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            
            logger.info(f"Stored {len(points)} embeddings in batch")
            
        except Exception as e:
            logger.error(f"Failed to store embeddings batch: {str(e)}")
            raise
    
    def search_similar(
        self,
        query_vector: List[float],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search using query_points.
        
        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            
        Returns:
            List of search results with payload and score
        """
        try:
            results = self.client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                limit=limit
            ).points
            
            search_results = []
            for result in results:
                search_results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })
            
            logger.info(f"Found {len(search_results)} similar results")
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search: {str(e)}")
            raise
    
    def delete_file_embeddings(self, file_id: str) -> None:
        """
        Delete all embeddings for a specific file.
        
        Args:
            file_id: Google Drive file ID
        """
        try:
            self.client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="file_id",
                            match=MatchValue(value=file_id)
                        )
                    ]
                )
            )
            
            logger.info(f"Deleted embeddings for file: {file_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete embeddings: {str(e)}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            info = self.client.get_collection(collection_name=COLLECTION_NAME)
            return {
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {str(e)}")
            return {}


# Global Qdrant service instance
qdrant_service = QdrantService()
