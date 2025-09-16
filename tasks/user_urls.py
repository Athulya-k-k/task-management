# Create tasks/user_urls.py
from django.urls import path
from . import user_views

urlpatterns = [
    path('', user_views.user_tasks, name='user_tasks'),
    path('tasks/', user_views.user_tasks, name='user_tasks_dashboard'),
]
