from django.urls import path
from . import web_views

urlpatterns = [
    path('', web_views.dashboard, name='admin_dashboard'),
    path('login/', web_views.login_view, name='admin_login'),
    path('logout/', web_views.logout_view, name='admin_logout'),
    path('users/', web_views.manage_users, name='manage_users'),
    path('users/delete/<int:user_id>/', web_views.delete_user, name='delete_user'),
    path('users/assign/<int:user_id>/<int:admin_id>/', web_views.assign_user_to_admin, name='assign_user_to_admin'),
    path('tasks/', web_views.manage_tasks, name='manage_tasks'),
    path('tasks/<int:task_id>/', web_views.view_task, name='view_task'),
    path('tasks/<int:task_id>/complete/', web_views.complete_task, name='complete_task'),
    path('reports/', web_views.task_reports, name='task_reports'),
]