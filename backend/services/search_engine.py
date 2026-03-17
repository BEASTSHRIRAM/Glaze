"""Search engine for semantic similarity search."""
import logging
import time
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from cachetools import TTLCache

from services.embedding_service import EmbeddingService
from services.qdrant_service import QdrantService
from database import get_file_metadata

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with file metadata and relevance score."""
    file_id: str
    file_name: str
    mime_type: str
    link: str
    chunk_text: str
    score: float
    chunk_index: int = 0


class SearchEngine:
    """Semantic search engine using vector similarity."""
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        qdrant_service: QdrantService
    ):
        """
        Initialize search engine.
        
        Args:
            embedding_service: Embedding generation service
            qdrant_service: Qdrant vector database service
        """
        self.embedding_service = embedding_service
        self.qdrant_service = qdrant_service
        # Cache for query embeddings (5 minute TTL)
        self.query_cache = TTLCache(maxsize=100, ttl=300)
    
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Perform semantic search.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            
        Returns:
            List of SearchResult objects ranked by relevance
        """
        start_time = time.time()
        
        try:
            # Generate query embedding (with caching)
            if query in self.query_cache:
                logger.info("Using cached query embedding")
                query_embedding = self.query_cache[query]
            else:
                logger.info(f"Generating embedding for query: {query[:50]}...")
                query_embedding = self.embedding_service.generate_query_embedding(query)
                self.query_cache[query] = query_embedding
            
            # Perform vector similarity search
            logger.info(f"Searching for top {limit} similar results")
            qdrant_results = self.qdrant_service.search_similar(query_embedding, limit)
            
            # Fetch complete metadata and build results
            search_results = []
            for result in qdrant_results:
                payload = result['payload']
                file_id = payload.get('file_id')
                
                # Get complete file metadata from SQLite
                file_meta = get_file_metadata(file_id)
                
                if file_meta:
                    search_result = SearchResult(
                        file_id=file_id,
                        file_name=file_meta['file_name'],
                        mime_type=file_meta['mime_type'],
                        link=file_meta['link'],
                        chunk_text=payload.get('chunk_text', ''),
                        score=result['score'],
                        chunk_index=payload.get('chunk_index', 0)
                    )
                    search_results.append(search_result)
                else:
                    logger.warning(f"Metadata not found for file_id: {file_id}")
            
            query_time = int((time.time() - start_time) * 1000)
            logger.info(f"Search completed in {query_time}ms, found {len(search_results)} results")
            
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise
    
    def search_dict(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Perform search and return results as dict.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            
        Returns:
            Dict with results list and query_time_ms
        """
        start_time = time.time()
        
        results = self.search(query, limit)
        query_time = int((time.time() - start_time) * 1000)
        
        return {
            'results': [asdict(r) for r in results],
            'query_time_ms': query_time
        }


# Global search engine instance (will be initialized with services)
search_engine: SearchEngine = None


def initialize_search_engine(
    embedding_service: EmbeddingService,
    qdrant_service: QdrantService
) -> SearchEngine:
    """Initialize global search engine instance."""
    global search_engine
    search_engine = SearchEngine(embedding_service, qdrant_service)
    return search_engine
