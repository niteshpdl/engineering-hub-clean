from django.db.models import Q
from django.shortcuts import render
from notes.models import Resource, Project
from user_profiles.models import Profile
from django.contrib.auth.models import User

def search_view(request):
    query = request.GET.get('q', '')
    results = {
        'users': [],
        'resources': [],
        'projects': [],
        'query': query
    }
    
    if query:
        # Search for users
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        )
        
        # Get profiles for these users
        profiles = Profile.objects.filter(user__in=users)
        
        # Search for resources
        resources = Resource.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        ).order_by('-uploaded_at')
        
        # Search for projects
        projects = Project.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(team_members__icontains=query)
        ).order_by('-created_at')
        
        results['users'] = profiles
        results['resources'] = resources
        results['projects'] = projects
        
    return render(request, 'search/search_results.html', results)
