import os
import sys
from typing import List

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.embedding_service import embedding_service
from services.file_processor import file_processor

def test_embeddings():
    print("Testing Gemini Embedding 2.0 Integration...")
    
    # 1. Test single text embedding
    text = "Hello, this is a test of the Gemini Embedding 2.0 model."
    emb = embedding_service.generate_embedding(text)
    print(f"Single text embedding dims: {len(emb)}")
    assert len(emb) == 768, f"Expected 768 dims, got {len(emb)}"
    
    # 2. Test batch embedding
    texts = ["First text", "Second text", "Third text"]
    batch_embs = embedding_service.generate_embeddings_batch(texts, batch_size=2)
    print(f"Batch embedding count: {len(batch_embs)}")
    assert len(batch_embs) == 3
    assert len(batch_embs[0]) == 768
    
    # 3. Test query embedding
    query = "Search query"
    query_emb = embedding_service.generate_query_embedding(query)
    print(f"Query embedding dims: {len(query_emb)}")
    assert len(query_emb) == 768

    # 4. Test multimodal detection
    assert file_processor.is_multimodal("image/jpeg")
    assert file_processor.is_multimodal("audio/mp3")
    assert not file_processor.is_multimodal("text/plain")
    print("Multimodal detection: PASS")

    print("\nAll integration tests passed locally (simulated)!")
    print("Note: Actual API calls require a valid GEMINI_API_KEY and network access.")

if __name__ == "__main__":
    try:
        test_embeddings()
    except Exception as e:
        print(f"Verification failed: {e}")
        sys.exit(1)
