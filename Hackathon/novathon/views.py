from django.views import View
import os,json,ollama
from PyPDF2 import PdfReader
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pymilvus import connections, Collection
from llmware.models import ModelCatalog
from .case_searcher import CaseFileSearcher  # Assuming your provided code is saved as case_searcher.py in the same app directory
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from .models import RenamedCaseFile  # Make sure the model is imported
from .llllmware import interact_with_model
from django.views.decorators.http import require_POST

def search_case_files_view(request):
    # Initialize the searcher
    case_searcher = CaseFileSearcher()

    # Extract parameters from request body
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except ValueError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        query = data.get('query', None)
        year = data.get('year', None)
        criminal_name = data.get('criminal_name', None)
        police_station = data.get('police_station', None)
        crime_type = data.get('crime_type', None)
        top_k = data.get('top_k', 5)
    else:
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    # Convert year to integer if it exists
    if year:
        try:
            year = int(year)
        except ValueError:
            return JsonResponse({'error': 'Invalid year parameter'}, status=400)

    # Convert top_k to integer if it exists
    try:
        top_k = int(top_k)
    except ValueError:
        return JsonResponse({'error': 'Invalid top_k parameter'}, status=400)

    # Perform the search
    try:
        results = case_searcher.search_case_files(
            query=query,
            year=year,
            criminal_name=criminal_name,
            police_station=police_station,
            crime_type=crime_type,
            top_k=top_k
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    # Add file path to each result
    enriched_results = []
    for result in results:
        case_file_id = result.get('case_file_id')
        try:
            renamed_case_file = RenamedCaseFile.objects.get(case_id=case_file_id)
            result['file_path'] = renamed_case_file.file_path
        except ObjectDoesNotExist:
            result['file_path'] = None  # If file path is not found, set it as None

        enriched_results.append(result)

    # Return the enriched results as JSON
    return JsonResponse({'results': enriched_results}, safe=False)

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF file.
    """
    if not os.path.exists(file_path):
        return None, f"File not found: {file_path}"
    
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()  # Extract text from each page
        return text.strip(), None
    except Exception as e:
        return None, str(e)

def get_file_text(request, case_id):
    """
    View to get the file_path for a given case_id, extract text from PDF, and return the result.
    """
    # Get the RenamedCaseFile object or return 404
    renamed_case_file = get_object_or_404(RenamedCaseFile, case_id=case_id)
    
    # Extract file_path from the model
    file_path = renamed_case_file.file_path
    
    # Extract text from the file
    extracted_text, error = extract_text_from_pdf(file_path)
    summarizer=interact_with_model(context=extracted_text)
    if error:
        return JsonResponse({"error": error}, status=400)
    
    return JsonResponse({
        "case_id": case_id,
        "file_path": file_path,
        "extracted_text": summarizer
    })





class MilvusOllamaHandler:
    def __init__(self, collection_name='ipc_sections', host='localhost', port='19530'):
        connections.connect(host=host, port=port)
        self.collection = Collection(collection_name)
        self.collection.load()

    def generate_embedding(self, text):
        """Generate embedding using Ollama's mxbai-embed-large model"""
        response = ollama.embeddings(
            model='mxbai-embed-large',
            prompt=text
        )
        return response['embedding']

    def search_similar(self, query_text, top_k=5):
        """Search for similar documents based on query"""
        query_embedding = self.generate_embedding(query_text)

        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }

        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["description", "offense", "punishment", "section"]
        )

        similar_docs = []
        for hits in results:
            for hit in hits:
                similar_docs.append({
                    "id": hit.id,
                    "score": hit.distance,
                    "description": hit.entity.get("description"),
                    "offense": hit.entity.get("offense"),
                    "punishment": hit.entity.get("punishment"),
                    "section": hit.entity.get("section")
                })

        return similar_docs

    def close(self):
        """Close Milvus connection"""
        connections.disconnect("default")

@csrf_exempt
@require_POST
def legal_analysis_view(request):
    """
    Django view to perform legal analysis based on crime description
    
    Expected JSON payload:
    {
        "query": "crime description here"
    }
    """
    try:
        # Parse request body
        data = json.loads(request.body)
        query = data.get('query', '')

        if not query:
            return JsonResponse({
                'error': 'No query provided'
            }, status=400)

        # Initialize Milvus-Ollama handler
        handler = MilvusOllamaHandler()

        try:
            # Search for similar legal documents
            results = handler.search_similar(query)

            if not results:
                return JsonResponse({
                    'error': 'No similar legal documents found'
                }, status=404)

            # Register and load Ollama model
            ModelCatalog().register_ollama_model(
                model_name="llama3.2:latest",
                model_type="chat",
                host="localhost",
                port=11434,
                temperature=0
            )
            model = ModelCatalog().load_model("llama3.2:latest",temperature=0)

            # Prepare detailed analysis for the first result
            result = results[0]
            # print( {result['punishment']})
            # print(print(f"Description: {result['description']}"))
            # print(f"offense: {result['offense']}")
            # print({result['section']})
            llm_prompt = f"""As a seasoned legal advisor, you possess deep knowledge of legal intricacies and are skilled in referencing relevant laws and regulations. Users will seek guidance on various legal matters.

If a question falls outside the scope of legal expertise, kindly inform the user that your specialization is limited to legal advice.

In cases where you're uncertain of the answer, it's important to uphold integrity by admitting 'I don't know' rather than providing potentially erroneous information.

Below is a snippet of context from the relevant section of the constitution, although it will not be disclosed to users. the conext contain's the data about punishment and ipc sections etc ..


Question: {query}
Context: {result['punishment']}, {result['section']}


Your response should consist solely of helpful advice without any extraneous details.

Helpful advice:
"""

            # Get LLM analysis
            llm_response = model.inference(llm_prompt)

            # Close Milvus connection
            handler.close()

            # Prepare response
            return JsonResponse({
                'query': query,
                'similar_documents': results,
                'legal_analysis': llm_response
            })

        except Exception as search_error:
            handler.close()
            return JsonResponse({
                'error': f'Error during search or analysis: {str(search_error)}'
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Unexpected error: {str(e)}'
        }, status=500)

