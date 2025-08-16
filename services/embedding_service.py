from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union

class EmbeddingService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize embedding service with sentence transformer model"""
        self.model_name = model_name
        self.model = None
        # Don't load model immediately - load on first use
    
    def _load_model(self):
        """Load the sentence transformer model"""
        if self.model is not None:
            return
        
        try:
            print(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            print("✅ Embedding model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
            raise e
    
    def encode_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """Convert text to embeddings"""
        if not self.model:
            self._load_model()
        
        try:
            # Handle single string or list of strings
            if isinstance(text, str):
                text = [text]
            
            # Generate embeddings
            embeddings = self.model.encode(text, convert_to_numpy=True)
            
            return embeddings
        
        except Exception as e:
            print(f"Embedding generation failed: {e}")
            raise e
    
    def encode_query(self, query: str) -> np.ndarray:
        """Encode search query into embedding"""
        return self.encode_text(query)[0]  # Return single embedding
    
    def encode_documents(self, documents: List[str]) -> np.ndarray:
        """Encode multiple documents into embeddings"""
        return self.encode_text(documents)
    
    def calculate_similarity(self, query_embedding: np.ndarray, document_embeddings: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity between query and documents"""
        try:
            # Normalize embeddings
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            doc_norms = document_embeddings / np.linalg.norm(document_embeddings, axis=1, keepdims=True)
            
            # Calculate cosine similarity
            similarities = np.dot(doc_norms, query_norm)
            
            return similarities
        
        except Exception as e:
            print(f"Similarity calculation failed: {e}")
            return np.array([])
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this model"""
        if not self.model:
            return 384  # Default for all-MiniLM-L6-v2
        
        # Generate a test embedding to get dimension
        test_embedding = self.encode_text("test")
        return test_embedding.shape[1]