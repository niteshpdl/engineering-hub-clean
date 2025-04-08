from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Count, Q
import json
from .models import Profile
from django.views.decorators.http import require_POST
from .models import Profile, Comment, ProfileComment
from django.contrib.auth.views import LoginView
from .forms import UserLoginForm

from notes.models import Resource, Project, Vote, Comment as ResourceComment
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, ProfileForm


from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm
from .models import Profile  # Make sure to import your Profile model

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create or update profile
            profile, created = Profile.objects.get_or_create(user=user)
            
            # Handle profile picture upload
            if 'profile_picture' in request.FILES:
                profile.image = request.FILES['profile_picture']
            
            # Handle other profile fields if they exist in your form
            if 'dob' in form.cleaned_data:
                profile.dob = form.cleaned_data.get('dob')
            if 'address' in form.cleaned_data:
                profile.address = form.cleaned_data.get('address')
            if 'contact' in form.cleaned_data:
                profile.contact = form.cleaned_data.get('contact')
                
            profile.save()
            
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')  # Redirect to login instead of home
    else:
        form = UserRegisterForm()
    
    return render(request, 'user_profiles/user_templates/register.html', {'form': form})


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import UserUpdateForm, ProfileUpdateForm
from .models import Profile, ProfileComment
from notes.models import Resource  # Adjust this import based on your project structure

@login_required
def profile(request):
    print("Profile view reached!")
    
    # Get or create the user's profile
    try:
        profile = request.user.user_profiles_profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)

    # Get user resources with vote counts
    username = request.user.username
    profile_user = get_object_or_404(User, username=username)
    resources = Resource.objects.filter(uploader=request.user).order_by('-uploaded_at')
    
    # Get profile comments
    profile_comments = ProfileComment.objects.filter(profile_user=profile_user).order_by('-created_at')

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'resources': resources,
        'profile_comments': profile_comments,
        'profile_user': profile_user,  # Add this for the template
        'user_profile': profile,  # Add this for the template
    }
    
    return render(request, 'user_profiles/user_templates/profile.html', context)

@login_required
def user_detail(request, username):
    user = get_object_or_404(User, username=username)
    
    # Get resources with vote counts
    resources = Resource.objects.filter(uploader=user).order_by('-uploaded_at')
    
    profile_comments = ProfileComment.objects.filter(profile_user=user)

    
    # Check if logged-in user has voted on any of these resources
    if request.user.is_authenticated:
        user_votes = Vote.objects.filter(
            user=request.user, 
            resource__in=resources
        ).values_list('resource_id', 'vote_type')
        user_votes_dict = {res_id: vote_type for res_id, vote_type in user_votes}
    else:
        user_votes_dict = {}
        
    context = {
        'profile_user': user,
        'resources': resources,
        'user_votes': user_votes_dict,
        'profile_comments': profile_comments,
    }
    
    return render(request, 'user_profiles/profile.html', context)


@login_required
def profile_resources(request):
    resources = Resource.objects.filter(uploader=request.user).order_by('-uploaded_at')
    
    # Get vote statistics
    for resource in resources:
        resource.comment_count = ResourceComment.objects.filter(resource=resource).count()
    
    return render(request, 'user_profiles/profile_resources.html', {'resources': resources})


@login_required
def profile_projects(request):
    projects = Project.objects.filter(uploader=request.user).order_by('-uploaded_at')
    return render(request, 'user_profiles/profile_projects.html', {'projects': projects})


@login_required
def delete_resource(request, resource_id):
    """Delete a resource if the user is the uploader"""
    resource = get_object_or_404(Resource, pk=resource_id)
    
    if request.user != resource.uploader:
        messages.error(request, "You don't have permission to delete this resource.")
        return redirect('profile')
        
    if request.method == 'POST':
        resource.delete()
        messages.success(request, "Resource deleted successfully!")
        return redirect('profile_resources')
        
    return render(request, 'user_profiles/confirm_delete.html', {'resource': resource})


def resource_detail(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    comments = ResourceComment.objects.filter(resource=resource).order_by('-created_at')
    
    # Get user's vote if they are logged in
    user_vote = None
    if request.user.is_authenticated:
        try:
            vote = Vote.objects.get(user=request.user, resource=resource)
            user_vote = vote.vote_type
        except Vote.DoesNotExist:
            pass
    
    context = {
        'resource': resource,
        'comments': comments,
        'user_vote': user_vote,
    }
    
    return render(request, 'resource_detail.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, 
                                  request.FILES, 
                                  instance=request.user.user_profiles_profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.user_profiles_profile)
    
    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    
    return render(request, 'edit_profile.html', context)


# New Profile Comment Functions
@login_required
def add_profile_comment(request, profile_user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=profile_user_id)
        profile = get_object_or_404(Profile, user=target_user)
        
        text = request.POST.get('comment_text')
        if text:
            ProfileComment.objects.create(
                author=request.user,
                profile=profile,
                text=text
            )
            messages.success(request, 'Comment added successfully!')
        else:
            messages.error(request, 'Comment cannot be empty!')
            
        # Redirect based on whose profile we're viewing
        if target_user == request.user:
            return redirect('profile')
        else:
            return redirect('user_detail', username=target_user.username)
    
    return redirect('home')


@login_required
def edit_profile_comment(request, comment_id):
    comment = get_object_or_404(ProfileComment, id=comment_id)
    
    # Only the author can edit their comment
    if request.user != comment.author:
        return JsonResponse({'success': False, 'error': 'You do not have permission to edit this comment'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text')
            
            if text:
                comment.text = text
                comment.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Comment cannot be empty'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def delete_profile_comment(request, comment_id):
    comment = get_object_or_404(ProfileComment, id=comment_id)
    
    # Either the profile owner or comment author can delete
    if request.user != comment.author and request.user != comment.profile.user:
        return JsonResponse({'success': False, 'error': 'You do not have permission to delete this comment'})
    
    if request.method == 'POST':
        comment.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@require_POST
def add_profile_comment(request, profile_user_id):
    profile_user = get_object_or_404(User, id=profile_user_id)
    text = request.POST.get('comment_text')
    
    if text:
        ProfileComment.objects.create(
            profile_user=profile_user,
            author=request.user,
            text=text
        )
    
    return redirect('profile', username=profile_user.username)


@login_required
@require_POST
def delete_profile_comment(request, comment_id):
    comment = get_object_or_404(ProfileComment, id=comment_id)
    
    # Only the author or the profile owner can delete a comment
    if request.user != comment.author and request.user != comment.profile_user:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    try:
        comment.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

class CustomLoginView(LoginView):
    form_class = UserLoginForm
    template_name = 'user_profiles/user_templates/login.html'
    
    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')
        if not remember_me:
            # Session expires when browser closes
            self.request.session.set_expiry(0)
        else:
            # Session expires after 2 weeks (in seconds)
            self.request.session.set_expiry(1209600)
        
        return super().form_valid(form)