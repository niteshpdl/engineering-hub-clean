from django.urls import path
from . import views
from notes.search import search_view


urlpatterns = [
    path('', views.home, name='home'),
    path('departments/<str:resource_type>/<str:resource_name>/', views.departments_view, name='departments_view'),
    path('resources/<int:department_id>/<int:semester_id>/<str:resource_type>/', views.resources_list, name='resource_list'),
    path('resource/<int:resource_id>/', views.resource_detail, name='resource_detail'),
    path('resource/<int:resource_id>/vote/', views.resource_vote, name='resource_vote'),
    path('resource/<int:resource_id>/comment/', views.add_comment, name='add_comment'),
    path('upload/resource/', views.upload_resource, name='upload_resource'),
    path('api/departments/<int:department_id>/semesters/', views.department_semesters_api, name='department_semesters_api'),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
    path('resource/<int:resource_id>/delete/', views.delete_resource, name='delete_resource'),
    
    # Project URLs - these should be defined only here
    path('projects/', views.project_categories, name='projects'),  # Categories overview
    path('projects/<str:category>/', views.project_list, name='project_list'),  # List projects in a category
    path('projects/detail/<int:project_id>/', views.project_detail, name='project_detail'),  # Project detail
    path('upload/project/', views.upload_project, name='upload_project'),  # Upload project
    path('debug/project-model/', views.debug_model, name='debug_model'),
    path('projects/inspect/<int:project_id>/', views.inspect_project, name='inspect_project'),
    path('inspect-db/', views.inspect_db, name='inspect_db'),
    path('search/', search_view, name='search'),
    
]
