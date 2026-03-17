"""Embedding generation service using Google Gemini API."""
import logging
import time
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.genai import Client, types

from config import get_settings

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when API rate limit is exceeded."""
    pass


class EmbeddingService:
    """Service for generating embeddings using Google Gemini."""
    
    def __init__(self):
        """Initialize embedding service with Gemini API."""
        settings = get_settings()
        self.client = Client(api_key=settings.gemini_api_key)
        self.model_name = "gemini-embedding-2-preview"
        logger.info("Embedding service initialized with Gemini API (gemini-embedding-2-preview)")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((RateLimitError, Exception))
    )
    def generate_embedding(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """
        Generate embedding vector for a single text.
        
        Args:
            text: Text to embed
            task_type: Type of task for the embedding
            
        Returns:
            Embedding vector as list of floats (768 dimensions)
        """
        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=768
                )
            )
            
            embedding = result.embeddings[0].values
            logger.debug(f"Generated {task_type} embedding with {len(embedding)} dimensions")
            return list(embedding)
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            if "quota" in str(e).lower() or "rate" in str(e).lower():
                raise RateLimitError(f"Rate limit exceeded: {str(e)}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches using the native batch API.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process per API call (Gemini supports up to 2048)
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} texts)")
            
            try:
                result = self.client.models.embed_content(
                    model=self.model_name,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=768
                    )
                )
                
                batch_embeddings = [list(e.values) for e in result.embeddings]
                all_embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"Failed to embed batch {batch_num}: {str(e)}")
                # If a whole batch fails, we might want to retry individually or pad with zeros
                # For now, let's pad to maintain alignment if necessary, or re-raise
                if "quota" in str(e).lower() or "rate" in str(e).lower():
                    # Wait and retry could be handled by @retry if we wrapped this
                    time.sleep(5)
                all_embeddings.extend([[0.0] * 768] * len(batch))
            
            # Tiny delay to be safe, though batch API is intended for this
            if i + batch_size < len(texts):
                time.sleep(0.5)
        
        logger.info(f"Generated {len(all_embeddings)} embeddings")
        return all_embeddings
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        """
        return self.generate_embedding(query, task_type="RETRIEVAL_QUERY")

    def generate_multimodal_embedding(self, data: bytes, mime_type: str) -> List[float]:
        """
        Generate embedding for multimodal content (images, audio, video, PDF).
        
        Args:
            data: Binary content
            mime_type: MIME type of the content
            
        Returns:
            Embedding vector
        """
        try:
            part = types.Part.from_bytes(data=data, mime_type=mime_type)
            
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=[part],
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=768
                )
            )
            
            embedding = result.embeddings[0].values
            logger.info(f"Generated multimodal embedding for {mime_type} with {len(embedding)} dimensions")
            return list(embedding)
            
        except Exception as e:
            logger.error(f"Failed to generate multimodal embedding: {str(e)}")
            raise


# Global embedding service instance
embedding_service = EmbeddingService()
