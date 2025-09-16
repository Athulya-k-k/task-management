from django.urls import path
from . import user_views

urlpatterns = [
    # Main user interface (SPA)
    path('', user_views.user_tasks, name='user_tasks'),
    path('app/', user_views.user_tasks, name='user_tasks_app'),
    
    # Authentication
    path('login/', user_views.user_login, name='user_login'),
    path('logout/', user_views.user_logout, name='user_logout'),
    
    # Dashboard and main views
    path('dashboard/', user_views.user_dashboard, name='user_dashboard'),
    path('profile/', user_views.user_profile, name='user_profile'),
    
    # Task management
    path('tasks/', user_views.user_task_list, name='user_task_list'),
    path('tasks/<int:task_id>/', user_views.user_task_detail, name='user_task_detail'),
    path('tasks/<int:task_id>/complete/', user_views.complete_task, name='user_complete_task'),
    path('tasks/<int:task_id>/update-status/', user_views.update_task_status, name='user_update_task_status'),
    path('history/', user_views.user_task_history, name='user_task_history'),
    
    # AJAX endpoints for the SPA
    path('ajax/tasks/<int:task_id>/complete/', user_views.complete_task_ajax, name='ajax_complete_task'),
    path('ajax/stats/', user_views.get_task_stats, name='ajax_task_stats'),
    path('ajax/upcoming-tasks/', user_views.get_upcoming_tasks, name='ajax_upcoming_tasks'),
]