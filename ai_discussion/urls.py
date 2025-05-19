from django.urls import path
from . import views

app_name = 'ai_discussion'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('discussions/', views.discussions_list, name='discussions_list'),
    path('discussion/<int:discussion_id>/', views.discussion_detail, name='discussion_detail'),
    path('discussion/<int:discussion_id>/delete/', views.delete_discussion, name='delete_discussion'),
    path('api/discussion/start/', views.start_discussion, name='start_discussion'),
    path('api/discussion/<int:discussion_id>/status/', views.get_discussion_status, name='get_discussion_status'),
    path('api/discussion/<int:discussion_id>/stop/', views.stop_discussion, name='stop_discussion'),
    path('api/user/discussions/', views.user_discussions, name='user_discussions'),
    path('api/user/migrate-local-discussions/', views.migrate_local_discussions, name='migrate_local_discussions'),
    path('api/debug/auth/', views.auth_debug, name='auth_debug'),
] 