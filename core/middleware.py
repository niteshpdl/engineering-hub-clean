from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs that can be accessed without authentication
        self.public_urls = [
            reverse('login'),
            reverse('register'),
            reverse('admin:index'),
            # Add other public URLs as needed
        ]
        
    def __call__(self, request):
        if not request.user.is_authenticated and request.path_info not in self.public_urls \
           and not request.path_info.startswith(settings.STATIC_URL) \
           and not request.path_info.startswith(settings.MEDIA_URL) \
           and not request.path_info.startswith('/admin/'):
            return redirect(settings.LOGIN_URL)
            
        response = self.get_response(request)
        return response
