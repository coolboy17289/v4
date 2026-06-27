"""
FAISS Vector Database Manager
"""

import logging
import numpy as np
import os
import pickle
from typing import List, Dict, Any, Optional, Tuple
import faiss

logger = logging.getLogger(__name__)


class FAISSManager:
    """Manages FAISS index for vector storage and retrieval"""

    def __init__(self, dimension: int = 384, index_type: str = "IndexFlatL2"):
        """
        Initialize the FAISS manager

        Args:
            dimension: Dimension of the vectors
            index_type: Type of FAISS index to use
        """
        self.dimension = dimension
        self.index_type = index_type
        self.index = None
        self.id_to_doc_map: Dict[int, Dict[str, Any]] = {}
        self.next_id = 0

        self._initialize_index()

    def _initialize_index(self):
        """Initialize the FAISS index based on the specified type"""
        try:
            if self.index_type == "IndexFlatL2":
                self.index = faiss.IndexFlatL2(self.dimension)
            elif self.index_type == "IndexFlatIP":
                self.index = faiss.IndexFlatIP(self.dimension)
            elif self.index_type == "IndexIVFFlat":
                # For IVF, we need a quantizer
                quantizer = faiss.IndexFlatL2(self.dimension)
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)  # 100 clusters
                # We'll need to train this index before adding vectors
                self.needs_training = True
            else:
                # Default to FlatL2
                logger.warning(f"Unknown index type {self.index_type}, defaulting to IndexFlatL2")
                self.index = faiss.IndexFlatL2(self.dimension)

            logger.info(f"Initialized FAISS index: {self.index_type} with dimension {self.dimension}")

        except Exception as e:
            logger.error(f"Failed to initialize FAISS index: {str(e)}")
            raise

    def add_vectors(self, vectors: np.ndarray, documents: List[Dict[str, Any]]):
        """
        Add vectors to the index with associated document metadata

        Args:
            vectors: NumPy array of shape (n, dimension) containing vectors to add
            documents: List of document dictionaries corresponding to each vector
        """
        try:
            if len(vectors) != len(documents):
                raise ValueError("Number of vectors must match number of documents")

            # Train the index if needed (for IVF indices)
            if hasattr(self, 'needs_training') and self.needs_training:
                logger.info("Training IVF index...")
                self.index.train(vectors)
                self.needs_training = False

            # Add vectors to the index
            start_id = self.next_id
            self.index.add(vectors.astype('float32'))

            # Store the document mappings
            for i, doc in enumerate(documents):
                self.id_to_doc_map[start_id + i] = doc

            self.next_id += len(vectors)
            logger.info(f"Added {len(vectors)} vectors to the index. Total vectors: {self.next_id}")

        except Exception as e:
            logger.error(f"Failed to add vectors to index: {str(e)}")
            raise

    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar vectors

        Args:
            query_vector: Query vector of shape (1, dimension) or (dimension,)
            k: Number of results to return

        Returns:
            List of dictionaries containing the documents and their scores
        """
        try:
            # Ensure query vector is 2D
            if query_vector.ndim == 1:
                query_vector = query_vector.reshape(1, -1)

            # Perform search
            distances, indices = self.index.search(query_vector.astype('float32'), k)

            # Prepare results
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx == -1:  # FAISS returns -1 for empty slots
                    continue

                doc = self.id_to_doc_map.get(int(idx))
                if doc is None:
                    continue

                result = {
                    "document": doc,
                    "distance": float(distance),
                    "similarity": 1.0 / (1.0 + float(distance)),  # Simple conversion to similarity
                    "rank": i + 1
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Failed to search index: {str(e)}")
            raise

    def save_index(self, filepath: str):
        """
        Save the index and metadata to disk

        Args:
            filepath: Base path for saving (will create .index and .pkl files)
        """
        try:
            # Save the FAISS index
            faiss.write_index(self.index, f"{filepath}.index")

            # Save the ID to document map
            with open(f"{filepath}_metadata.pkl", 'wb') as f:
                pickle.dump({
                    'id_to_doc_map': self.id_to_doc_map,
                    'next_id': self.next_id,
                    'dimension': self.dimension,
                    'index_type': self.index_type
                }, f)

            logger.info(f"Saved index to {filepath}.index and metadata to {filepath}_metadata.pkl")

        except Exception as e:
            logger.error(f"Failed to save index: {str(e)}")
            raise

    def load_index(self, filepath: str):
        """
        Load the index and metadata from disk

        Args:
            filepath: Base path for loading (expects .index and _metadata.pkl files)
        """
        try:
            # Load the FAISS index
            self.index = faiss.read_index(f"{filepath}.index")

            # Load the metadata
            with open(f"{filepath}_metadata.pkl", 'rb') as f:
                data = pickle.load(f)
                self.id_to_doc_map = data['id_to_doc_map']
                self.next_id = data['next_id']
                # Optionally verify dimension and index_type match
                if self.dimension != data['dimension']:
                    logger.warning(f"Dimension mismatch: expected {self.dimension}, got {data['dimension']}")
                if self.index_type != data['index_type']:
                    logger.warning(f"Index type mismatch: expected {self.index_type}, got {data['index_type']}")

            logger.info(f"Loaded index from {filepath}.index with {self.next_id} vectors")

        except Exception as e:
            logger.error(f"Failed to load index: {str(e)}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the index

        Returns:
            Dictionary with index statistics
        """
        return {
            "total_vectors": self.next_id,
            "dimension": self.dimension,
            "index_type": self.index_type,
            "is_trained": getattr(self.index, 'is_trained', True)
        }

    def clear(self):
        """Clear the index and reset"""
        self._initialize_index()
        self.id_to_doc_map.clear()
        self.next_id = 0
        logger.info("Cleared the vector index")