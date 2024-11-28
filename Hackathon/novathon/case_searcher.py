import pandas as pd
import ollama
from pymilvus import Collection, connections
import numpy as np

class OllamaEmbedding:
    def __init__(self, model_name='mxbai-embed-large'):
        self.model_name = model_name
    
    def encode(self, texts):
        """
        Generate embeddings using Ollama
        
        :param texts: Single text or list of texts
        :return: Embedding vector(s)
        """
        # Handle single text input
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = []
        for text in texts:
            response = ollama.embeddings(
                model=self.model_name,
                prompt=text
            )
            # Ensure the embedding is exactly 768 dimensions
            embedding = response['embedding']
            if len(embedding) != 768:
                # Pad or truncate to exactly 768 dimensions
                embedding = np.array(embedding)
                if len(embedding) > 768:
                    embedding = embedding[:768]
                else:
                    embedding = np.pad(embedding, (0, 768 - len(embedding)), mode='constant')
            
            embeddings.append(embedding.tolist())
        
        # Return single embedding if only one text, otherwise return list
        return embeddings[0] if len(embeddings) == 1 else embeddings

class CaseFileSearcher:
    def __init__(self, embedding_model='mxbai-embed-large'):
        # Initialize Ollama embedding model
        self.embedding_model = OllamaEmbedding(embedding_model)
        
        # Milvus connection setup
        self.connect_to_milvus()
        
    def connect_to_milvus(self):
        # Connect to Milvus
        connections.connect(host='localhost', port='19530')
        
        # Load existing collection
        self.collection = Collection('case_files')
        self.collection.load()
    
    def search_case_files(self, 
                          query=None, 
                          year=None, 
                          criminal_name=None, 
                          police_station=None, 
                          crime_type=None, 
                          top_k=5):
        """
        Search case files with multiple filtering options
        
        :param query: Semantic search query
        :param year: Specific year to filter
        :param criminal_name: Criminal name to filter
        :param police_station: Police station to filter
        :param crime_type: Type of crime to filter
        :param top_k: Number of top results to return
        :return: Retrieved case files
        """
        # Prepare search conditions
        search_params = {
            'metric_type': 'L2',
            'params': {'nprobe': 10}
        }
        
        # Build filter conditions
        bool_expr = []
        if year:
            bool_expr.append(f"year == {year}")
        if criminal_name:
            bool_expr.append(f"criminal_name == '{criminal_name}'")
        if police_station:
            bool_expr.append(f"police_station == '{police_station}'")
        if crime_type:
            bool_expr.append(f"crime_type == '{crime_type}'")
        
        filter_expr = " and ".join(bool_expr) if bool_expr else None
        
        # Semantic search with optional embedding
        if query:
            query_embedding = self.embedding_model.encode(query)
            
            results = self.collection.search(
                data=[query_embedding],
                anns_field='case_embedding',
                param=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=['case_file_id', 'year', 'criminal_name', 'police_station', 'crime_type', 'case_details']
            )
        else:
            # If no query, perform metadata-only search
            results = self.collection.search(
                data=[[0]*768],  # Dummy embedding (match your model's dimension)
                anns_field='case_embedding',
                param=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=['case_file_id', 'year', 'criminal_name', 'police_station', 'crime_type', 'case_details']
            )
        
        # Process and return case files
        retrieved_case_files = []
        for result in results[0]:
            case_file = {
                'case_file_id': result.entity.get('case_file_id'),
                'year': result.entity.get('year'),
                'criminal_name': result.entity.get('criminal_name'),
                'police_station': result.entity.get('police_station'),
                'crime_type': result.entity.get('crime_type'),
                'case_details': result.entity.get('case_details')
            }
            retrieved_case_files.append(case_file)
        
        return retrieved_case_files