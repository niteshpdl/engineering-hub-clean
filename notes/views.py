from django.shortcuts import render, redirect, get_object_or_404
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Resource, Department, Semester, Vote, Comment
from django.core.paginator import PageNotAnInteger, EmptyPage
from .forms import ResourceUploadForm, CommentForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.models import User
from .models import Resource, Project
from user_profiles.models import Profile, ProfileComment 
from django.shortcuts import redirect
from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('home')  # Redirect to your home page after logout

# filepath: c:\Users\DELL\Desktop\Minor Project\user_profiles\views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User

def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    return render(request, 'user_profiles/user_templates/profile.html', {'user': user})

def home(request):
    """Homepage showing recent resources and most popular items"""
    recent_resources = Resource.objects.all().order_by('-uploaded_at')[:10]
    popular_resources = Resource.objects.all().order_by('-upvotes')[:10]
    
    context = {
        'recent_resources': recent_resources,
        'popular_resources': popular_resources,
        'departments': Department.objects.all()
    }
    return render(request, 'home.html', context)


@login_required
def vote_resource(request):
    if request.method == 'POST':
        resource_id = request.POST.get('resource_id')
        vote_type = request.POST.get('vote_type')
        
        if not resource_id or not vote_type:
            return JsonResponse({'error': 'Missing parameters'}, status=400)
            
        try:
            resource = Resource.objects.get(id=resource_id)
            user = request.user
            
            # Check if the user has already voted
            try:
                vote = Vote.objects.get(user=user, resource=resource)
                if vote.vote_type == vote_type:
                    # If voting the same way, remove the vote
                    vote.delete()
                    user_vote = None
                else:
                    # Change vote type
                    vote.vote_type = vote_type
                    vote.save()
                    user_vote = vote_type
            except Vote.DoesNotExist:
                # Create new vote
                Vote.objects.create(user=user, resource=resource, vote_type=vote_type)
                user_vote = vote_type
            
            # Update the resource counts
            upvotes = Vote.objects.filter(resource=resource, vote_type='upvote').count()
            downvotes = Vote.objects.filter(resource=resource, vote_type='downvote').count()
            
            # Update resource counts
            resource.upvotes = upvotes
            resource.downvotes = downvotes
            resource.save()
            
            # Return updated counts and user's current vote status
            return JsonResponse({
                'upvotes': upvotes,
                'downvotes': downvotes,
                'user_vote': user_vote
            })
        except Resource.DoesNotExist:
            return JsonResponse({'error': 'Resource not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def add_comment(request, profile_user_id):
    if request.method == 'POST':
        profile_user = get_object_or_404(User, id=profile_user_id)
        profile = get_object_or_404(Profile, user=profile_user)
        
        text = request.POST.get('comment_text')
        if text:
            Comment.objects.create(
                author=request.user,
                profile=profile,
                text=text
            )
            messages.success(request, 'Comment added successfully!')
        else:
            messages.error(request, 'Comment cannot be empty!')
            
        # Redirect back to the profile page
        return redirect('profile' if profile_user == request.user else 'user_detail', username=profile_user.username)
    
    return redirect('home')
@login_required
@require_POST
def resource_vote(request, resource_id):
    """Handle voting on resources (upvote/downvote)"""
    resource = get_object_or_404(Resource, id=resource_id)
    vote_type = request.POST.get('vote_type')
    
    if vote_type not in ['upvote', 'downvote']:
        return JsonResponse({'error': 'Invalid vote type'}, status=400)
    
    # Check if user has already voted on this resource
    existing_vote = Vote.objects.filter(user=request.user, resource=resource).first()
    
    if existing_vote:
        if existing_vote.vote_type == vote_type:
            # If voting the same way, remove the vote (toggle off)
            existing_vote.delete()
        else:
            # Change vote type
            existing_vote.vote_type = vote_type
            existing_vote.save()
    else:
        # Create new vote
        Vote.objects.create(user=request.user, resource=resource, vote_type=vote_type)
    
    # Get updated vote counts
    upvotes = Vote.objects.filter(resource=resource, vote_type='upvote').count()
    downvotes = Vote.objects.filter(resource=resource, vote_type='downvote').count()
    
    # Update resource vote counts
    resource.upvotes = upvotes
    resource.downvotes = downvotes
    resource.save()
    
    return JsonResponse({
        'success': True,
        'upvotes': upvotes,
        'downvotes': downvotes,
    })

@login_required
def resource_detail(request, resource_id):
    """Display resource details"""
    resource = get_object_or_404(Resource, id=resource_id)
    comments = Comment.objects.filter(resource=resource).order_by('-created_at')
    comment_form = CommentForm()
    
    # Check if user has voted on this resource
    user_vote = None
    if request.user.is_authenticated:
        vote = Vote.objects.filter(user=request.user, resource=resource).first()
        if vote:
            user_vote = vote.vote_type
    
    context = {
        'resource': resource,
        'comments': comments,
        'comment_form': comment_form,
        'user_vote': user_vote,
    }
    
    return render(request, 'resources/resource_detail.html', context)


@login_required
def upload_resource(request):
    if request.method == 'POST':
        # Get form data
        resource_type = request.POST.get('resource_type')
        title = request.POST.get('title')
        description = request.POST.get('description')
        department_id = request.POST.get('department')
        semester_id = request.POST.get('semester')
        file = request.FILES.get('file')
        thumbnail = request.FILES.get('thumbnail')
        
        # Validate required fields
        if not all([resource_type, title, description, department_id, semester_id, file]):
            messages.error(request, "Please fill all required fields")
            return redirect('upload_resource')
        
        try:
            # Get related objects
            department = Department.objects.get(id=department_id)
            semester = Semester.objects.get(id=semester_id)
            
            # Create resource - Changed 'user' to 'uploader'
            resource = Resource(
                uploader=request.user,  # Changed from 'user' to 'uploader'
                resource_type=resource_type,
                title=title,
                description=description,
                department=department,
                semester=semester,
                file=file,
                thumbnail=thumbnail
            )
            resource.save()
            
            messages.success(request, "Resource uploaded successfully!")
            return redirect('resource_detail', resource_id=resource.id)
            
        except Exception as e:
            messages.error(request, f"Error uploading resource: {str(e)}")
            return redirect('upload_resource')
    
    # GET request - show the form
    departments = Department.objects.all()
    return render(request, 'upload.html', {'departments': departments})

def departments_view(request, resource_type=None, resource_name=None):
    """View to display all departments for a specific resource type"""
    departments = Department.objects.all().order_by('name')
    
    # Set default resource type and name if not provided
    if not resource_type:
        resource_type = 'notes'
    
    if not resource_name:
        resource_types = {
            'notes': 'Notes',
            'papers': 'Question Papers',
            'books': 'Books and References',
            'projects': 'Projects',
        }
        resource_name = resource_types.get(resource_type, 'Resources')
    
    context = {
        'departments': departments,
        'resource_type': resource_type,
        'resource_name': resource_name,
    }
    
    return render(request, 'resources/departments.html', context)

def department_semesters_api(request, department_id):
    try:
        department = Department.objects.get(id=department_id)
        semesters = Semester.objects.filter(department=department).order_by('number')
        
        semesters_data = [
            {'id': semester.id, 'number': semester.number}
            for semester in semesters
        ]
        
        return JsonResponse({'semesters': semesters_data})
    except Department.DoesNotExist:
        return JsonResponse({'error': 'Department not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def department_detail(request, dept_id):
    """View to display department details and its semesters"""
    department = get_object_or_404(Department, id=dept_id)
    semesters = Semester.objects.filter(department=department).order_by('number')
    
    # Count resources by type
    resources_by_type = {
        'notes': Resource.objects.filter(department=department, resource_type='notes').count(),
        'handwritten': Resource.objects.filter(department=department, resource_type='handwritten').count(),
        'insight': Resource.objects.filter(department=department, resource_type='insight').count(),
        'syllabus': Resource.objects.filter(department=department, resource_type='syllabus').count()
    }
    
    context = {
        'department': department,
        'semesters': semesters,
        'resources_by_type': resources_by_type
    }
    
    return render(request, 'department_detail.html', context)

# Add this function to your notes/views.py file

def semester_detail(request, semester_id):
    """View to display semester details and its resources"""
    semester = get_object_or_404(Semester, id=semester_id)
    department = semester.department
    
    # Get resources by type for this semester
    resources_by_type = {
        'notes': Resource.objects.filter(semester=semester, resource_type='notes').count(),
        'handwritten': Resource.objects.filter(semester=semester, resource_type='handwritten').count(),
        'insight': Resource.objects.filter(semester=semester, resource_type='insight').count(),
        'syllabus': Resource.objects.filter(semester=semester, resource_type='syllabus').count()
    }
    
    # Get subjects for this semester (if you have a Subject model)
    # subjects = Subject.objects.filter(semester=semester)
    
    context = {
        'semester': semester,
        'department': department,
        'resources_by_type': resources_by_type,
        # 'subjects': subjects,
    }
    
    return render(request, 'semester_detail.html', context)

# Add this function to your notes/views.py file

def semesters_view(request, department_id):
    """View to display all semesters for a specific department"""
    department = get_object_or_404(Department, id=department_id)
    semesters = Semester.objects.filter(department=department).order_by('number')
    
    context = {
        'department': department,
        'semesters': semesters,
    }
    
    return render(request, 'semesters.html', context)

# Resource type-specific department views referenced in department_detail.html

def notes_department(request, department_id):
    """View for notes resources by department"""
    department = get_object_or_404(Department, id=department_id)
    semesters = Semester.objects.filter(department=department).order_by('number')
    
    context = {
        'department': department,
        'semesters': semesters,
        'resource_type': 'notes',
        'resource_name': 'Notes'
    }
    
    return render(request, 'resources/semesters.html', context)


def handwritten_department(request, department_id):
    """View for handwritten resources by department"""
    department = get_object_or_404(Department, id=department_id)
    semesters = Semester.objects.filter(department=department).order_by('number')
    
    context = {
        'department': department,
        'semesters': semesters,
        'resource_type': 'handwritten',
        'resource_name': 'Handwritten Notes'
    }
    
    return render(request, 'resources/semesters.html', context)


def insights_department(request, department_id):
    """View for insights resources by department"""
    department = get_object_or_404(Department, id=department_id)
    semesters = Semester.objects.filter(department=department).order_by('number')
    
    context = {
        'department': department,
        'semesters': semesters,
        'resource_type': 'insight',
        'resource_name': 'Insights'
    }
    
    return render(request, 'resources/semesters.html', context)


def syllabus_department(request, department_id):
    """View for syllabus resources by department"""
    department = get_object_or_404(Department, id=department_id)
    semesters = Semester.objects.filter(department=department).order_by('number')
    
    context = {
        'department': department,
        'semesters': semesters,
        'resource_type': 'syllabus',
        'resource_name': 'Syllabus'
    }
    
    return render(request, 'resources/semesters.html', context)


# Resource list views for specific resource types

def notes_list(request, department_id, semester_id):
    """View to display notes for a specific department and semester"""
    department = get_object_or_404(Department, id=department_id)
    semester = get_object_or_404(Semester, id=semester_id)
    
    resources = Resource.objects.filter(
        department=department,
        semester=semester,
        resource_type='notes'
    ).order_by('-uploaded_at')
    
    # Pagination
    paginator = Paginator(resources, 9)  # 9 resources per page
    page = request.GET.get('page')
    resources = paginator.get_page(page)
    
    context = {
        'resources': resources,
        'department': department,
        'semester': semester,
        'resource_type': 'notes',
        'resource_name': 'Notes',
    }
    
    return render(request, 'resources/list.html', context)


def handwritten_list(request, department_id, semester_id):
    """View to display handwritten notes for a specific department and semester"""
    department = get_object_or_404(Department, id=department_id)
    semester = get_object_or_404(Semester, id=semester_id)
    
    resources = Resource.objects.filter(
        department=department,
        semester=semester,
        resource_type='handwritten'
    ).order_by('-uploaded_at')
    
    # Pagination
    paginator = Paginator(resources, 9)  # 9 resources per page
    page = request.GET.get('page')
    resources = paginator.get_page(page)
    
    context = {
        'resources': resources,
        'department': department,
        'semester': semester,
        'resource_type': 'handwritten',
        'resource_name': 'Handwritten Notes',
    }
    
    return render(request, 'resources/list.html', context)


def insights_list(request, department_id, semester_id):
    """View to display insights for a specific department and semester"""
    department = get_object_or_404(Department, id=department_id)
    semester = get_object_or_404(Semester, id=semester_id)
    
    resources = Resource.objects.filter(
        department=department,
        semester=semester,
        resource_type='insight'
    ).order_by('-uploaded_at')
    
    # Pagination
    paginator = Paginator(resources, 9)  # 9 resources per page
    page = request.GET.get('page')
    resources = paginator.get_page(page)
    
    context = {
        'resources': resources,
        'department': department,
        'semester': semester,
        'resource_type': 'insight',
        'resource_name': 'Insights',
    }
    
    return render(request, 'resources/list.html', context)


def syllabus_list(request, department_id, semester_id):
    """View to display syllabus for a specific department and semester"""
    department = get_object_or_404(Department, id=department_id)
    semester = get_object_or_404(Semester, id=semester_id)
    
    resources = Resource.objects.filter(
        department=department,
        semester=semester,
        resource_type='syllabus'
    ).order_by('-uploaded_at')
    
    # Pagination
    paginator = Paginator(resources, 9)  # 9 resources per page
    page = request.GET.get('page')
    resources = paginator.get_page(page)
    
    context = {
        'resources': resources,
        'department': department,
        'semester': semester,
        'resource_type': 'syllabus',
        'resource_name': 'Syllabus',
    }
    
    return render(request, 'resources/list.html', context)


# You might also need a delete resource view

@login_required
def delete_resource(request, resource_id):
    """Delete a resource"""
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if user is the uploader or an admin
    if request.user == resource.uploader or request.user.is_staff:
        if request.method == 'POST':
            # Delete the resource
            resource.delete()
            messages.success(request, "Resource deleted successfully.")
            return redirect('home')
        
        # GET request shows confirmation page
        return render(request, 'resources/delete_confirm.html', {'resource': resource})
    else:
        messages.error(request, "You don't have permission to delete this resource.")
        return redirect('resource_detail', resource_id=resource_id)


# User profile view

@login_required
def user_profile(request, username=None):
    """Display user profile with their uploaded resources"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if username:
        profile_user = get_object_or_404(User, username=username)
    else:
        profile_user = request.user
    
    # Get resources uploaded by this user
    resources = Resource.objects.filter(uploader=profile_user).order_by('-uploaded_at')
    
    # Pagination
    paginator = Paginator(resources, 10)
    page = request.GET.get('page')
    resources = paginator.get_page(page)
    
    context = {
        'profile_user': profile_user,
        'resources': resources,
        'is_own_profile': request.user == profile_user
    }
    
    return render(request, 'user/profile.html', context)


@login_required
def delete_resource(request, resource_id):
    """Delete a resource if the current user is the uploader"""
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if the user is the uploader of the resource
    if resource.uploader != request.user:
        messages.error(request, "You don't have permission to delete this resource")
        return redirect('resource_detail', resource_id=resource_id)
    
    # Store the resource title for feedback message
    resource_title = resource.title
    
    # Delete the resource
    resource.delete()
    
    messages.success(request, f'Resource "{resource_title}" has been deleted.')
    
    # Redirect to profile resources page
    return redirect('profile_resources')

# Search view

def search_resources(request):
    """Search for resources"""
    query = request.GET.get('q', '')
    resource_type = request.GET.get('type', None)
    department_id = request.GET.get('department', None)
    semester_id = request.GET.get('semester', None)
    
    resources = Resource.objects.all()
    
    # Apply filters
    if query:
        resources = resources.filter(title__icontains=query)
    
    if resource_type:
        resources = resources.filter(resource_type=resource_type)
    
    if department_id:
        resources = resources.filter(department_id=department_id)
    
    if semester_id:
        resources = resources.filter(semester_id=semester_id)
    
    # Get all departments and semesters for filter dropdowns
    departments = Department.objects.all()
    semesters = Semester.objects.all()
    
    # Pagination
    paginator = Paginator(resources, 12)
    page = request.GET.get('page')
    resources = paginator.get_page(page)
    
    context = {
        'resources': resources,
        'query': query,
        'departments': departments,
        'semesters': semesters,
        'selected_type': resource_type,
        'selected_department': department_id,
        'selected_semester': semester_id
    }
    
    return render(request, 'resources/search.html', context)

# Add this alias at the end of your views.py file to fix the first error
#resources_list = resource_list  # Create an alias for backward compatibility

# Add the projects view function
def projects(request):
    query = request.GET.get('q', '')
    
    if query:
        projects_list = Project.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        ).order_by('-uploaded_at')
    else:
        projects_list = Project.objects.all().order_by('-uploaded_at')
    
    paginator = Paginator(projects_list, 9)  # Show 9 projects per page
    page = request.GET.get('page')
    
    try:
        projects = paginator.page(page)
    except PageNotAnInteger:
        projects = paginator.page(1)
    except EmptyPage:
        projects = paginator.page(paginator.num_pages)
    
    # Update this line to use the correct template path based on your structure
    return render(request, 'projects/list.html', {'projects': projects})

# Add this function for any other resource types that might be referenced in urls.py
def departments(request):
    """View to display all departments"""
    departments = Department.objects.all().order_by('name')
    
    context = {
        'departments': departments,
    }
    
    return render(request, 'departments.html', context)

# Make sure you have a project_categories view, not a projects view
def project_categories(request):
    """View to display project categories"""
    # Get count of projects in each category
    categories = [
        {
            'id': 'ai',  # This must be a valid non-empty string
            'name': 'AI Projects',
            'icon': 'fa-robot',
            'count': Project.objects.filter(category='ai').count(),
        },
        {
            'id': 'ml',
            'name': 'ML Projects',
            'icon': 'fa-brain',
            'count': Project.objects.filter(category='ml').count(),
        },
        {
            'id': 'iot',
            'name': 'IoT Projects',
            'icon': 'fa-microchip',
            'count': Project.objects.filter(category='iot').count(),
        },
        {
            'id': 'software',
            'name': 'Software Projects',
            'icon': 'fa-laptop-code',
            'count': Project.objects.filter(category='software').count(),
        },
        {
            'id': 'major',
            'name': 'Major Projects',
            'icon': 'fa-project-diagram',
            'count': Project.objects.filter(category='major').count(),
        },
        {
            'id': 'minor',
            'name': 'Minor Projects',
            'icon': 'fa-tasks',
            'count': Project.objects.filter(category='minor').count(),
        },
    ]
    
    print("Rendering categories.html with:", categories)
    return render(request, 'projects/categories.html', {'categories': categories})

def project_list(request, category):
    """View for listing projects by category"""
    # Get search query if provided
    query = request.GET.get('q', '')
    
    # Filter by category (NOT type)
    projects_list = Project.objects.filter(category=category)
    
    # Get category name for display
    category_display = {
        'ai': 'AI Projects',
        'ml': 'ML Projects',
        'iot': 'IoT Projects',
        'major': 'Major Projects',
        'minor': 'Minor Projects',
        'software': 'Software Projects',
    }.get(category, f"{category.title()} Projects")
    
    # Filter by search query if provided
    if query:
        projects_list = projects_list.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # Order by newest first
    projects_list = projects_list.order_by('-created_at')
    
    # Debug print
    print(f"Category: {category}, Projects found: {projects_list.count()}")
    
    # Paginate results
    paginator = Paginator(projects_list, 9)  # 9 projects per page
    page = request.GET.get('page')
    
    try:
        projects = paginator.page(page)
    except PageNotAnInteger:
        projects = paginator.page(1)
    except EmptyPage:
        projects = paginator.page(paginator.num_pages)
    
    context = {
        'projects': projects,
        'category': category,
        'category_display': category_display,
        'query': query,
    }
    
    return render(request, 'projects/list.html', context)

def search(request):
    """Search view for resources"""
    query = request.GET.get('q', '')
    
    if query:
        resources = Resource.objects.filter(title__icontains=query)
    else:
        resources = Resource.objects.none()
    
    # Pagination
    paginator = Paginator(resources, 12)
    page = request.GET.get('page')
    resources = paginator.get_page(page)
    
    context = {
        'query': query,
        'resources': resources,
    }
    
    return render(request, 'resources/search.html', context)

def about(request):
    """About page"""
    return render(request, 'about.html')

def contact(request):
    """Contact page"""
    return render(request, 'contact.html')

def faq(request):
    """FAQ page"""
    return render(request, 'faq.html')

def privacy(request):
    """Privacy policy page"""
    return render(request, 'privacy.html')

def terms(request):
    """Terms of service page"""
    return render(request, 'terms.html')

def resources_list(request, department_id, semester_id, resource_type):
    """View to display resources for a specific department and semester"""
    department = get_object_or_404(Department, id=department_id)
    semester = get_object_or_404(Semester, id=semester_id)
    
    resources = Resource.objects.filter(
        department=department,
        semester=semester,
        resource_type=resource_type
    ).order_by('-uploaded_at')
    
    # Add this code to properly set the resource name based on resource_type
    resource_names = {
        'notes': 'Notes',
        'handwritten': 'Handwritten Notes',
        'insight': 'Insights',
        'syllabus': 'Syllabus'
    }
    resource_name = resource_names.get(resource_type, resource_type.capitalize())
    
    # Pagination
    paginator = Paginator(resources, 9)  # 9 resources per page
    page = request.GET.get('page')
    resources = paginator.get_page(page)
    
    context = {
        'resources': resources,
        'department': department,
        'semester': semester,
        'resource_type': resource_type,
        'resource_name': resource_name,  # Now properly set
    }
    
    return render(request, 'resources/list.html', context)
def project_detail(request, project_id):
    """View for showing project details"""
    project = get_object_or_404(Project, id=project_id)
    
    context = {
        'project': project,
    }
    
    return render(request, 'projects/detail.html', context)

@login_required
def upload_project(request):
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        category = request.POST.get('category')  # Use category, not type
        documentation = request.FILES.get('documentation')  # Use documentation, not file
        team_members = request.POST.get('team_members', '')
        supervisor = request.POST.get('supervisor', '')
        
        # Validate required fields
        errors = []
        if not title:
            errors.append('Project title is required.')
        if not category:
            errors.append('Project category is required.')
        if not documentation:
            errors.append('Documentation file is required.')
            
        # If no errors, save the project
        if not errors:
            try:
                project = Project.objects.create(
                    title=title,
                    description=description,
                    category=category,  # Use category, not type
                    documentation=documentation,
                    team_members=team_members,
                    supervisor=supervisor,
                    author=request.user
                )
                messages.success(request, 'Your project has been uploaded successfully!')
                
                # Redirect to project detail page
                return redirect('project_detail', project_id=project.id)
            except Exception as e:
                print(f"Error saving project: {str(e)}")
                messages.error(request, f'Error uploading project: {str(e)}')
        else:
            for error in errors:
                messages.error(request, error)
    
    # Get categories for the form
    categories = Project.CATEGORY_CHOICES if hasattr(Project, 'CATEGORY_CHOICES') else [
        ('ai', 'AI Projects'),
        ('ml', 'ML Projects'),
        ('iot', 'IoT Projects'),
        ('software', 'Software Projects'),
        ('major', 'Major Projects'),
        ('minor', 'Minor Projects'),
    ]
    
    return render(request, 'projects/upload.html', {'categories': categories})

@login_required
@require_POST
def upvote_resource(request, resource_id):
    """Handle upvoting a resource"""
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if user already voted
    existing_vote = Vote.objects.filter(resource=resource, user=request.user).first()
    
    if existing_vote:
        # If already upvoted, remove vote (toggle off)
        if existing_vote.vote_type == 'upvote':
            existing_vote.delete()
            message = 'Your upvote has been removed'
        else:
            # Change from downvote to upvote
            existing_vote.vote_type = 'upvote'
            existing_vote.save()
            message = 'Changed to upvote'
    else:
        # Create new upvote
        Vote.objects.create(
            resource=resource,
            user=request.user,
            vote_type='upvote'
        )
        message = 'Your upvote has been recorded'
    
    # Update the counters
    resource.update_vote_counts()
    
    if request.is_ajax():
        return JsonResponse({
            'upvotes': resource.upvotes, 
            'downvotes': resource.downvotes,
            'message': message
        })
    else:
        return redirect('resource_detail', resource_id=resource_id)

@login_required
@require_POST
def downvote_resource(request, resource_id):
    """Handle downvoting a resource"""
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if user already voted
    existing_vote = Vote.objects.filter(resource=resource, user=request.user).first()
    
    if existing_vote:
        # If already downvoted, remove vote (toggle off)
        if existing_vote.vote_type == 'downvote':
            existing_vote.delete()
            message = 'Your downvote has been removed'
        else:
            # Change from upvote to downvote
            existing_vote.vote_type = 'downvote'
            existing_vote.save()
            message = 'Changed to downvote'
    else:
        # Create new downvote
        Vote.objects.create(
            resource=resource,
            user=request.user,
            vote_type='downvote'
        )
        message = 'Your downvote has been recorded'
    
    # Update the counters
    resource.update_vote_counts()
    
    if request.is_ajax():
        return JsonResponse({
            'upvotes': resource.upvotes, 
            'downvotes': resource.downvotes,
            'message': message
        })
    else:
        return redirect('resource_detail', resource_id=resource_id)

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from .models import Resource, Department, Semester, Vote, Comment  # Remove profile_comments from here
from user_profiles.models import Profile, ProfileComment  # Import from user_profiles instead

def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    
    # Get the existing profile
    user_profile = get_object_or_404(Profile, user=user)
    
    # Get user resources
    resources = Resource.objects.filter(uploader=user).order_by('-uploaded_at')
    
    # Get profile comments for the viewed user
    profile_comments = ProfileComment.objects.filter(profile_user=user).order_by('-created_at')
    
    # Calculate total upvotes safely
    total_upvotes = sum(getattr(resource, 'upvotes', 0) for resource in resources)
    
    context = {
        'profile_user': user,  # Important: Set the profile_user
        'user_profile': user_profile,
        'resources': resources,  # Use the same variable name as in template
        'profile_comments': profile_comments,
        'total_upvotes': total_upvotes,
    }
    
    return render(request, 'user_profile/profile.html', context)

def register_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in after registration
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

from django.shortcuts import redirect

def redirect_resource_list(request, department_id, semester_id, resource_type):
    """Redirect from incorrect URL structure to the correct one"""
    if resource_type == 'notes':
        return redirect('notes_list', department_id=department_id, semester_id=semester_id)
    elif resource_type == 'handwritten':
        return redirect('handwritten_list', department_id=department_id, semester_id=semester_id)
    elif resource_type == 'insight':
        return redirect('insights_list', department_id=department_id, semester_id=semester_id)
    elif resource_type == 'syllabus':
        return redirect('syllabus_list', department_id=department_id, semester_id=semester_id)
    else:
        # Fallback to notes if resource type is unknown
        return redirect('notes_list', department_id=department_id, semester_id=semester_id)

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Only the author can edit
    if request.user != comment.author:
        return JsonResponse({'success': False, 'error': 'You do not have permission to edit this comment'})
    
    if request.method == 'POST':
        data = json.loads(request.body)
        text = data.get('text')
        
        if text:
            comment.text = text
            comment.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Comment cannot be empty'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Only the author can edit
    if request.user != comment.author:
        return JsonResponse({'success': False, 'error': 'You do not have permission to edit this comment'})
    
    if request.method == 'POST':
        data = json.loads(request.body)
        text = data.get('text')
        
        if text:
            comment.text = text
            comment.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Comment cannot be empty'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def debug_model(request):
    """Debug view to examine the Project model structure"""
    from django.db import connection
    
    # Get table structure
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(notes_project)")
        columns = cursor.fetchall()
    
    # Get model fields
    model_fields = [
        {"name": field.name, "type": field.get_internal_type()}
        for field in Project._meta.fields
    ]
    
    # Get a sample project
    sample_project = Project.objects.first()
    project_data = None
    if sample_project:
        project_data = {key: str(value) for key, value in sample_project.__dict__.items() 
                      if not key.startswith('_')}
    
    context = {
        "table_columns": columns,
        "model_fields": model_fields,
        "project_data": project_data,
    }
    
    # Render as JSON for easy viewing
    from django.http import JsonResponse
    return JsonResponse(context, json_dumps_params={'indent': 2})

from django.http import JsonResponse

def inspect_project(request, project_id):
    """View to inspect a specific project's data structure"""
    project = get_object_or_404(Project, id=project_id)
    
    # Get model fields
    fields = [field.name for field in Project._meta.fields]
    
    # Get project data
    data = {}
    for field in fields:
        try:
            value = getattr(project, field)
            # Convert non-serializable objects to string representation
            if hasattr(value, '__dict__'):
                data[field] = str(value)
            else:
                data[field] = value
        except Exception as e:
            data[field] = f"Error: {str(e)}"
    
    return JsonResponse({
        'fields': fields,
        'data': data
    }, json_dumps_params={'indent': 2})

from django.http import HttpResponse
import json
from django.db import connection

def inspect_db(request):
    """Extremely simple view to inspect database schema using only raw SQL"""
    data = {}
    
    # Get tables
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        data["tables"] = [table[0] for table in tables]
    
    # Get Project table structure
    if 'notes_project' in data["tables"]:
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(notes_project);")
            columns = cursor.fetchall()
            # Column info format: (cid, name, type, notnull, dflt_value, pk)
            data["project_columns"] = [
                {"id": col[0], "name": col[1], "type": col[2], 
                 "required": bool(col[3]), "primary_key": bool(col[5])} 
                for col in columns
            ]
    
    # Get a sample row
    with connection.cursor() as cursor:
        try:
            cursor.execute("SELECT * FROM notes_project LIMIT 1;")
            row = cursor.fetchone()
            if row:
                # Make a dictionary of column name -> value
                sample_data = {}
                for i, col in enumerate(data["project_columns"]):
                    sample_data[col["name"]] = str(row[i])
                data["sample_project"] = sample_data
        except Exception as e:
            data["error"] = str(e)
    
    return HttpResponse(f"<pre>{json.dumps(data, indent=2)}</pre>", content_type="text/plain")

