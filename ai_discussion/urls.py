from django.urls import path
from . import views

app_name = 'ai_discussion'

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('discussions/', views.discussions_list, name='discussions_list'),
    path('discussion/<int:discussion_id>/', views.discussion_detail, name='discussion_detail'),
    
    # Authentication pages
    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('logout/', views.user_logout, name='logout'),
    
    # OAuth authentication
    path('auth/google/login/', views.google_auth, name='google_auth'),
    path('auth/google/callback/', views.google_auth_callback, name='google_auth_callback'),
    
    # Discussion management - accepts both form POST and API requests
    path('discussion/<int:discussion_id>/delete/', views.delete_discussion, name='delete_discussion'),
    path('discussion/start/', views.start_discussion, name='start_discussion'),  # For form submissions
    path('api/discussion/start/', views.start_discussion, name='api_start_discussion'),  # For API requests
    path('api/discussion/<int:discussion_id>/status/', views.get_discussion_status, name='get_discussion_status'),
    path('api/discussion/<int:discussion_id>/stop/', views.stop_discussion, name='stop_discussion'),
    
    # User data management
    path('api/user/discussions/', views.user_discussions, name='user_discussions'),
    path('api/user/migrate-local-discussions/', views.migrate_local_discussions, name='migrate_local_discussions'),
    
    # Character management
    path('characters/', views.manage_characters, name='manage_characters'),
    path('characters/create/', views.create_character, name='create_character'),
    path('characters/<int:character_id>/edit/', views.edit_character, name='edit_character'),
    path('characters/<int:character_id>/delete/', views.delete_character, name='delete_character'),
    
    # Participant selection
    path('api/participants/select/', views.select_participants, name='select_participants'),
    
    # Debug endpoints
    path('auth/debug/', views.auth_debug, name='auth_debug'),  # For form submissions
    path('api/debug/auth/', views.auth_debug, name='api_auth_debug'),  # For API requests
] 