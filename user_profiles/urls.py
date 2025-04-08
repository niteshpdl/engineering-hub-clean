from django.urls import path
from . import views
from user_profiles.views import CustomLoginView
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),    
    path('profile/resources/', views.profile_resources, name='profile_resources'),
    path('profile/projects/', views.profile_projects, name='profile_projects'),
    path('resource/<int:resource_id>/delete/', views.delete_resource, name='delete_resource'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),  # This should come before the catch-all pattern
    path('<str:username>/', views.user_detail, name='user_detail'),
    path('comments/<int:profile_user_id>/add/', views.add_profile_comment, name='add_profile_comment'),
    path('comments/<int:comment_id>/edit/', views.edit_profile_comment, name='edit_profile_comment'),
    path('comments/<int:comment_id>/delete/', views.delete_profile_comment, name='delete_profile_comment'),
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='user_profiles/user_templates/passwordreset.html'), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='user_profiles/user_templates/password_reset_done.html'), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='user_profiles/user_templates/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='user_profiles/user_templates/password_reset_complete.html'), 
         name='password_reset_complete'),

]
