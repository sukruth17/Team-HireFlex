from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .case_searcher import CaseFileSearcher  # Assuming your provided code is saved as case_searcher.py in the same app directory

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

    # Return the results as JSON
    return JsonResponse({'results': results}, safe=False)

