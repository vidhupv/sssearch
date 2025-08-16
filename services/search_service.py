import pymongo
import numpy as np
from typing import List, Dict, Any
import os
from .embedding_service import EmbeddingService

class SearchService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.client = None
        self.db = None
        self.collection = None
        self._connect_to_mongodb()
    
    def _connect_to_mongodb(self):
        """Connect to MongoDB Atlas"""
        try:
            # Get MongoDB connection string from environment
            mongo_uri = os.getenv('MONGODB_URI')
            if not mongo_uri:
                print("⚠️  MONGODB_URI not found, using local fallback storage")
                self.use_local_storage = True
                self.local_data = []
                return
            
            self.client = pymongo.MongoClient(mongo_uri)
            self.db = self.client['visual_memory_search']
            self.collection = self.db['screenshots']
            
            # Create vector search index if it doesn't exist
            self._ensure_vector_index()
            self.use_local_storage = False
            print("✅ Connected to MongoDB Atlas")
            
        except Exception as e:
            print(f"⚠️  MongoDB connection failed: {e}")
            print("📁 Using local storage fallback")
            self.use_local_storage = True
            self.local_data = []
    
    def _ensure_vector_index(self):
        """Create vector search index for MongoDB Atlas"""
        try:
            # Check if index exists
            indexes = list(self.collection.list_indexes())
            vector_index_exists = any(idx.get('name') == 'vector_index' for idx in indexes)
            
            if not vector_index_exists:
                # Create vector search index
                self.collection.create_index([
                    ("embedding", "2dsphere")
                ], name="vector_index")
                print("✅ Vector search index created")
        
        except Exception as e:
            print(f"Vector index creation failed: {e}")
    
    def store_screenshot(self, filename: str, image_data: str, ocr_text: str, 
                        visual_description: str, combined_text: str):
        """Store screenshot data with embeddings"""
        try:
            # Generate embedding for the combined text
            embedding = self.embedding_service.encode_text(combined_text)[0]
            
            document = {
                'filename': filename,
                'image_data': image_data,
                'ocr_text': ocr_text,
                'visual_description': visual_description,
                'combined_text': combined_text,
                'embedding': embedding.tolist()  # Convert numpy array to list
            }
            
            if self.use_local_storage:
                # Store locally
                self.local_data.append(document)
                print(f"📁 Stored {filename} locally")
            else:
                # Store in MongoDB
                self.collection.insert_one(document)
                print(f"💾 Stored {filename} in MongoDB")
        
        except Exception as e:
            print(f"Failed to store {filename}: {e}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar screenshots"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.encode_query(query)
            
            if self.use_local_storage:
                return self._search_local(query_embedding, top_k)
            else:
                return self._search_mongodb(query_embedding, top_k)
        
        except Exception as e:
            print(f"Search failed: {e}")
            return []
    
    def _search_local(self, query_embedding: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """Search using local storage with cosine similarity"""
        if not self.local_data:
            return []
        
        # Extract embeddings and calculate similarities
        document_embeddings = np.array([doc['embedding'] for doc in self.local_data])
        similarities = self.embedding_service.calculate_similarity(query_embedding, document_embeddings)
        
        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            doc = self.local_data[idx].copy()
            doc['score'] = float(similarities[idx])
            # Remove embedding from result to save space
            doc.pop('embedding', None)
            results.append(doc)
        
        return results
    
    def _search_mongodb(self, query_embedding: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """Search using MongoDB Atlas vector search"""
        try:
            # For now, we'll use a simple approach with cosine similarity
            # In a production setup, you'd use MongoDB Atlas Vector Search
            
            # Get all documents (for small datasets)
            documents = list(self.collection.find({}, {'_id': 0}))
            
            if not documents:
                return []
            
            # Calculate similarities
            document_embeddings = np.array([doc['embedding'] for doc in documents])
            similarities = self.embedding_service.calculate_similarity(query_embedding, document_embeddings)
            
            # Get top-k results
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                doc = documents[idx].copy()
                doc['score'] = float(similarities[idx])
                # Remove embedding from result
                doc.pop('embedding', None)
                results.append(doc)
            
            return results
        
        except Exception as e:
            print(f"MongoDB search failed: {e}")
            return []
    
    def get_total_screenshots(self) -> int:
        """Get total number of stored screenshots"""
        if self.use_local_storage:
            return len(self.local_data)
        else:
            try:
                return self.collection.count_documents({})
            except:
                return 0