import os
from PyPDF2 import PdfReader
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .case_searcher import CaseFileSearcher  # Assuming your provided code is saved as case_searcher.py in the same app directory
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from .models import RenamedCaseFile  # Make sure the model is imported
from .llllmware import interact_with_model
@csrf_exempt
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