from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import api_views

urlpatterns = [
    # JWT Authentication
    path('login/', api_views.LoginView.as_view(), name='api_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Tasks - Using APIView
    path('tasks/', api_views.UserTasksView.as_view(), name='get_user_tasks'),
    path('tasks/<int:task_id>/', api_views.UpdateTaskView.as_view(), name='update_task'),
    path('tasks/<int:task_id>/report/', api_views.TaskReportView.as_view(), name='task_report'),
    
]