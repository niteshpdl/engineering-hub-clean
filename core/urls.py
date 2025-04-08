from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from notes import views
from django.contrib.auth import views as auth_views
from user_profiles.views import CustomLoginView
from notes.views import logout_view

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),  # Path: /admin/
    
    # Include all URLs from the notes app
    path('', include('notes.urls')),
    
    # User profiles paths
    path('users/', include('user_profiles.urls')),
        
    # Authentication paths
    path('login/', auth_views.LoginView.as_view(template_name='user_profiles/user_templates/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),    
    # Home page
    path('', TemplateView.as_view(template_name='home.html'), name='home'),  # Path: /
    
    
    # Department listings
    path('departments/', views.departments_view, name='departments'),  # Path: /departments/
    path('departments/<int:dept_id>/', views.department_detail, name='department_detail'),  # Path: /departments/1/
    path('semester/<int:semester_id>/', views.semester_detail, name='semester_detail'),  # Path: /semester/1/
    
    # Redirect incorrect URL structure to correct structure
    path('resources/<int:department_id>/<int:semester_id>/<str:resource_type>/', views.redirect_resource_list, name='redirect_resource_list'),
    
    # Notes paths
    path('notes/', views.departments_view, {'resource_type': 'notes', 'resource_name': 'Notes'}, name='notes'),  # Path: /notes/
    path('notes/<int:department_id>/', views.semesters_view, {'resource_type': 'notes', 'resource_name': 'Notes'}, name='notes_department'),  # Path: /notes/1/
    path('notes/<int:department_id>/<int:semester_id>/', views.notes_list, name='notes_list'),  # Path: /notes/1/2/
    
    # Handwritten notes paths
    path('handwritten/', views.departments_view, {'resource_type': 'handwritten', 'resource_name': 'Handwritten Notes'}, name='handwritten'),  # Path: /handwritten/
    path('handwritten/<int:department_id>/', views.semesters_view, {'resource_type': 'handwritten', 'resource_name': 'Handwritten Notes'}, name='handwritten_department'),  # Path: /handwritten/1/
    path('handwritten/<int:department_id>/<int:semester_id>/', views.handwritten_list, name='handwritten_list'),  # Path: /handwritten/1/2/
    
    # Insight paths
    path('insight/', views.departments_view, {'resource_type': 'insight', 'resource_name': 'Insights'}, name='insights'),  # Path: /insight/
    path('insight/<int:department_id>/', views.semesters_view, {'resource_type': 'insight', 'resource_name': 'Insights'}, name='insight_department'),  # Path: /insight/1/
    path('insight/<int:department_id>/<int:semester_id>/', views.insights_list, name='insights_list'),  # Path: /insight/1/2/
    
    # Syllabus paths
    path('syllabus/', views.departments_view, {'resource_type': 'syllabus', 'resource_name': 'Syllabus'}, name='syllabus'),  # Path: /syllabus/
    path('syllabus/<int:department_id>/', views.semesters_view, {'resource_type': 'syllabus', 'resource_name': 'Syllabus'}, name='syllabus_department'),  # Path: /syllabus/1/
    path('syllabus/<int:department_id>/<int:semester_id>/', views.syllabus_list, name='syllabus_list'),  # Path: /syllabus/1/2/
    
    # Resource detail and interaction paths
    path('resources/<int:resource_id>/', views.resource_detail, name='resource_detail'),  # Path: /resources/1/
    path('resources/vote/', views.vote_resource, name='vote_resource'),  # Path: /resources/vote/
    path('resources/<int:resource_id>/comment/', views.add_comment, name='add_comment'),  # Path: /resources/1/comment/
    path('resources/<int:resource_id>/upvote/', views.upvote_resource, name='upvote_resource'),  # Path: /resources/1/upvote/
    path('resources/<int:resource_id>/downvote/', views.downvote_resource, name='downvote_resource'),  # Path: /resources/1/downvote/
    
    # Chatbot paths
    path('chatbot/', include('chatbot.urls', namespace='chatbot')),  # Path: /chatbot/
    
      
    # API paths
    path('api/departments/<int:department_id>/semesters/', views.department_semesters_api, name='department_semesters_api'),  # Path: /api/department/1/semesters/
    
    # Profile view path
    path('profile/<str:username>/', views.profile_view, name='profile_view'),  # Path: /profile/username/
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
