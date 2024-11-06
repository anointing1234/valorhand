from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponseServerError

class ErrorHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Handle 404 errors
        if response.status_code == 404:
            return render(request, '404.html', status=404)
        
        # Handle 500 errors (optional: you can customize this further)
        if response.status_code == 500:
            return render(request, '500.html', status=500)

        return response
