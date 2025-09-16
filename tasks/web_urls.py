from django.urls import path
from . import web_views

urlpatterns = [
    path('', web_views.dashboard, name='admin_dashboard'),
    path('login/', web_views.login_view, name='admin_login'),
    path('logout/', web_views.logout_view, name='admin_logout'),
    
    # User CRUD operations
    path('users/', web_views.manage_users, name='manage_users'),
    path('users/create/', web_views.create_user, name='create_user'),
    path('users/<int:user_id>/edit/', web_views.edit_user, name='edit_user'),
    path('users/<int:user_id>/view/', web_views.view_user, name='view_user'),
    path('users/<int:user_id>/delete/', web_views.delete_user, name='delete_user'),
    path('users/assign/<int:user_id>/<int:admin_id>/', web_views.assign_user_to_admin, name='assign_user_to_admin'),
    
    # Task CRUD operations
    path('tasks/', web_views.manage_tasks, name='manage_tasks'),
    path('tasks/create/', web_views.create_task, name='create_task'),
    path('tasks/<int:task_id>/', web_views.view_task, name='view_task'),
    path('tasks/<int:task_id>/edit/', web_views.edit_task, name='edit_task'),
    path('tasks/<int:task_id>/delete/', web_views.delete_task, name='delete_task'),
    path('tasks/<int:task_id>/complete/', web_views.complete_task, name='complete_task'),
    
    # Reports
    path('reports/', web_views.task_reports, name='task_reports'),
]