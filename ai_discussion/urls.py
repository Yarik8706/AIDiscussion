from django.urls import path
from . import views

app_name = 'ai_discussion'

urlpatterns = [
    path('', views.home, name='home'),
    path('discussions/', views.discussions_list, name='discussions_list'),
    path('discussion/<int:discussion_id>/', views.discussion_detail, name='discussion_detail'),
    path('api/discussion/start/', views.start_discussion, name='start_discussion'),
    path('api/discussion/<int:discussion_id>/status/', views.get_discussion_status, name='get_discussion_status'),
] 