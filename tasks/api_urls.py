from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import api_views

urlpatterns = [
   
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Tasks
    path('tasks/', api_views.get_user_tasks, name='get_user_tasks'),
    path('tasks/<int:task_id>/', api_views.update_task, name='update_task'),
    path('tasks/<int:task_id>/report/', api_views.get_task_report, name='get_task_report'),
]