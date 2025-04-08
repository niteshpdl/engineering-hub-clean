from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Change this to match what's used in the JavaScript
    path('api/session/', views.create_session, name='create_session'),
    # Or alternatively, update your JavaScript to use 'api/sessions/new/'
    
    path('api/message/', views.process_message, name='process_message'),
    path('api/upload_pdf/', views.upload_pdf, name='upload_pdf'),
    path('api/sessions/', views.get_sessions, name='get_sessions'),
    path('api/sessions/<str:session_id>/', views.get_session, name='get_session'),
    path('api/sessions/<str:session_id>/delete/', views.delete_session, name='delete_session'),
    path('api/test-handwritten/', views.test_handwritten_image, name='test_handwritten_image'),
    path('api/test-handwritten-pdf/', views.test_handwritten_pdf, name='test_handwritten_pdf'),
    path('test-handwritten/', views.test_handwritten_form, name='test_handwritten_form'),
]
