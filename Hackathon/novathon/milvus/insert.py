import pandas as pd
import ollama
from pymilvus import Collection, CollectionSchema, FieldSchema, DataType, connections
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

class CaseFileRAG:
    def __init__(self, embedding_model='mxbai-embed-large'):
        # Initialize Ollama embedding model
        self.embedding_model = OllamaEmbedding(embedding_model)
        
        # Milvus connection and collection setup
        self.setup_milvus_collection()
    
    def setup_milvus_collection(self):
        # Connect to Milvus
        connections.connect(host='localhost', port='19530')
        
        # Define expanded collection schema
        fields = [
            FieldSchema(name='case_file_id', dtype=DataType.INT64, is_primary=True),
            FieldSchema(name='year', dtype=DataType.INT64),
            FieldSchema(name='criminal_name', dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name='police_station', dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name='crime_type', dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name='case_details', dtype=DataType.VARCHAR, max_length=5000),
            FieldSchema(name='keywords', dtype=DataType.VARCHAR, max_length=500),
            # Adjust embedding dimension based on your Ollama model
            FieldSchema(name='case_embedding', dtype=DataType.FLOAT_VECTOR, dim=768)
        ]
        
        schema = CollectionSchema(fields)
        
        # Drop collection if it exists to avoid conflicts
        try:
            Collection('case_files').drop()
        except Exception:
            pass
        
        self.collection = Collection(name='case_files', schema=schema)
        
        # Create index
        index_params = {
            'metric_type': 'L2',
            'index_type': 'IVF_FLAT',
            'params': {'nlist': 1024}
        }
        self.collection.create_index(field_name='case_embedding', index_params=index_params)
    
    def load_case_files(self, case_files_path):
        # Read CSV file
        case_files_df = pd.read_csv(case_files_path)
        
        # Generate embeddings for case details with keywords
        case_files_df['combined_text'] = case_files_df['case_details'] + ' ' + case_files_df['keywords']
        case_files_df['case_embedding'] = case_files_df['combined_text'].apply(
            lambda x: self.embedding_model.encode(x)
        )
        
        # Verify embedding dimensions
        def validate_embedding(embedding):
            if len(embedding) != 768:
                raise ValueError(f"Embedding dimension is {len(embedding)}, expected 768")
            return embedding
        
        # Prepare data for insertion as a list of dictionaries
        insert_data = case_files_df.apply(lambda row: {
            'case_file_id': row['case_file_id'],
            'year': row['year'],
            'criminal_name': row['criminal_name'],
            'police_station': row['police_station'],
            'crime_type': row['crime_type'],
            'case_details': row['case_details'],
            'keywords': row['keywords'],
            'case_embedding': validate_embedding(row['case_embedding'])
        }, axis=1).tolist()
        
        # Insert data
        self.collection.insert(insert_data)
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
                output_fields=['case_file_id', 'year', 'criminal_name', 'police_station', 'crime_type', 'case_details', 'keywords']
            )
        else:
            # If no query, perform metadata-only search
            results = self.collection.search(
                data=[[0]*768],  # Dummy embedding (match your model's dimension)
                anns_field='case_embedding',
                param=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=['case_file_id', 'year', 'criminal_name', 'police_station', 'crime_type', 'case_details', 'keywords']
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
                'case_details': result.entity.get('case_details'),
                'keywords': result.entity.get('keywords')
            }
            retrieved_case_files.append(case_file)
        
        return retrieved_case_files

# Example Usage
def main():
    # Initialize and load case files from CSV
    rag_system = CaseFileRAG()
    rag_system.load_case_files('case_files_data.csv')
    
    # Example search scenarios
    print("Semantic Search for Financial Crimes:")
    semantic_results = rag_system.search_case_files(query="financial fraud")
    for result in semantic_results:
        print(f"Case File ID: {result['case_file_id']}")
        print(f"Year: {result['year']}")
        print(f"Criminal Name: {result['criminal_name']}")
        print(f"Police Station: {result['police_station']}")
        print(f"Crime Type: {result['crime_type']}")
        print(f"Keywords: {result['keywords']}")
        print(f"Case Details: {result['case_details']}")
        print("---")
    
    print("\nFiltered Search for Cybercrime in 2024:")
    year_crime_results = rag_system.search_case_files(year=2024, crime_type='Cybercrime')
    for result in year_crime_results:
        print(f"Case File ID: {result['case_file_id']}")
        print(f"Year: {result['year']}")
        print(f"Criminal Name: {result['criminal_name']}")
        print(f"Police Station: {result['police_station']}")
        print(f"Crime Type: {result['crime_type']}")
        print(f"Keywords: {result['keywords']}")
        print(f"Case Details: {result['case_details']}")
        print("---")

if __name__ == "__main__":
    main()