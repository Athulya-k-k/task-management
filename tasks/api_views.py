from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from .models import User, Task
from .serializers import (
    UserSerializer, LoginSerializer, TaskSerializer, 
    TaskUpdateSerializer, TaskReportSerializer
)
from django.contrib.auth import authenticate

class IsAdminOrSuperAdmin(permissions.BasePermission):
    """
    Custom permission to only allow admins and superadmins.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_admin() or request.user.is_superadmin())



@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_tasks(request):
    """
    GET /api/tasks - Fetch all tasks assigned to the logged-in user
    """
    tasks = Task.objects.filter(assigned_to=request.user)
    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_task(request, task_id):
    """
    PUT /api/tasks/{id} - Update task status with completion report and worked hours
    """
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    
    serializer = TaskUpdateSerializer(task, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(TaskSerializer(task).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def get_task_report(request, task_id):
    """
    GET /api/tasks/{id}/report - View completion report for admins and superadmins
    """
    task = get_object_or_404(Task, id=task_id)
    
    # Check if task is completed
    if task.status != 'completed':
        return Response(
            {'error': 'Task report is only available for completed tasks'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check permissions - admin can only see tasks they created or assigned to their users
    if request.user.is_admin():
        if task.created_by != request.user and task.assigned_to.assigned_admin != request.user:
            return Response(
                {'error': 'You do not have permission to view this task report'}, 
                status=status.HTTP_403_FORBIDDEN
            )
    
    serializer = TaskReportSerializer(task)
    return Response(serializer.data)