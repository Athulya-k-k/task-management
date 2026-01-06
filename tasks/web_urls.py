from django.urls import path
from . import web_views

urlpatterns = [
    # Dashboard and authentication
    path('', web_views.DashboardView.as_view(), name='admin_dashboard'),
    path('login/', web_views.LoginView.as_view(), name='admin_login'),
    path('logout/', web_views.LogoutView.as_view(), name='admin_logout'),
    
    # User management (SuperAdmin only)
    path('users/', web_views.ManageUsersView.as_view(), name='manage_users'),
    path('users/create/', web_views.CreateUserView.as_view(), name='create_user'),
    path('users/<int:user_id>/edit/', web_views.EditUserView.as_view(), name='edit_user'),
    path('users/<int:pk>/view/', web_views.ViewUserView.as_view(), name='view_user'),
    path('users/<int:user_id>/delete/', web_views.DeleteUserView.as_view(), name='delete_user'),
    path('users/assign/<int:user_id>/<int:admin_id>/', web_views.AssignUserToAdminView.as_view(), name='assign_user_to_admin'),
    
    # Task management (Admin and SuperAdmin)
    path('tasks/', web_views.ManageTasksView.as_view(), name='manage_tasks'),
    path('tasks/create/', web_views.CreateTaskView.as_view(), name='create_task'),
    path('tasks/<int:pk>/', web_views.ViewTaskView.as_view(), name='view_task'),
    path('tasks/<int:pk>/edit/', web_views.EditTaskView.as_view(), name='edit_task'),
    path('tasks/<int:pk>/delete/', web_views.DeleteTaskView.as_view(), name='delete_task')
,
    
    # Task reports (Admin and SuperAdmin)
    path('reports/', web_views.TaskReportsView.as_view(), name='task_reports'),
]