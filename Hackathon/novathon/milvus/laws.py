import csv
import ollama
from pymilvus import Collection, CollectionSchema, FieldSchema, DataType, connections, utility

class IPCRetriever:
    def __init__(self, host='localhost', port='19530', collection_name='ipc_sections'):
        # Connect to Milvus
        connections.connect(host=host, port=port)
        
        # Define collection schema
        fields = [
            FieldSchema(name='id', dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name='description', dtype=DataType.VARCHAR, max_length=5000),
            FieldSchema(name='offense', dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name='punishment', dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name='section', dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name='embedding', dtype=DataType.FLOAT_VECTOR, dim=1024)   # Ollama embedding dimension
        ]
        schema = CollectionSchema(fields)
        
        # Drop existing collection if it exists
        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
        
        # Create collection
        self.collection = Collection(name=collection_name, schema=schema)
        self.collection_name = collection_name

    def truncate_text(self, text, max_length=5000):
        """Truncate text to specified max length"""
        return text[:max_length]

    def load_data_from_csv(self, csv_path):
        """Load IPC data from CSV and create Milvus collection"""
        # Prepare data lists for batch insertion
        descriptions = []
        offenses = []
        punishments = []
        sections = []
        embeddings = []
        
        # Load data
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Truncate description
                truncated_description = self.truncate_text(row['Description'])
                
                # Generate embedding using Ollama
                embedding = ollama.embeddings(model='mxbai-embed-large', prompt=truncated_description)['embedding']
                
                # Append to lists
                descriptions.append(truncated_description)
                offenses.append(row['Offense'][:1000])
                punishments.append(row['Punishment'][:1000])
                sections.append(row['Section'][:100])
                embeddings.append(embedding)
        
        # Prepare data for batch insertion
        data = [descriptions, offenses, punishments, sections, embeddings]
        
        # Insert data
        self.collection.insert(data)
        
        # Create index for vector field
        index_params = {
            'metric_type': 'L2',
            'index_type': 'HNSW',
            'params': {'M': 8, 'efConstruction': 64}
        }
        self.collection.create_index(field_name='embedding', index_params=index_params)
        
        # Flush and load collection
        self.collection.flush()
        self.collection.load()

    def search_sections(self, query, top_k=3):
        """Retrieve most similar IPC sections based on query"""
        # Ensure collection is loaded
        self.collection.load()
        
        # Generate embedding for query
        query_embedding = ollama.embeddings(model='mxbai-embed-large', prompt=query)['embedding']
        
        # Search in Milvus
        search_params = {
            'metric_type': 'L2',
            'params': {'ef': 64}
        }
        results = self.collection.search(
            data=[query_embedding], 
            anns_field='embedding', 
            param=search_params, 
            limit=top_k,
            output_fields=['description', 'offense', 'punishment', 'section']
        )
        
        # Process and return results
        retrieved_sections = []
        for hits in results:
            for hit in hits:
                retrieved_sections.append({
                    'section': hit.entity.get('section'),
                    'description': hit.entity.get('description'),
                    'offense': hit.entity.get('offense'),
                    'punishment': hit.entity.get('punishment'),
                    'similarity_score': 1 / (1 + hit.distance)  # Convert distance to similarity
                })
        
        return retrieved_sections

# Example usage
if __name__ == '__main__':
    # Initialize retriever
    retriever = IPCRetriever()
    
    # Load data from CSV
    retriever.load_data_from_csv('ipc_sections.csv')
    
    # Example search
    query = "wearing military uniform"
    results = retriever.search_sections(query)
    
    # Print results
    for result in results:
        print(f"Section: {result['section']}")
        print(f"Description: {result['description']}")
        print(f"Similarity Score: {result['similarity_score']:.2f}\n")