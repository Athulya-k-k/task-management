from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from .models import User, Task
from .serializers import (
    UserSerializer, LoginSerializer, TaskSerializer, 
    TaskUpdateSerializer, TaskReportSerializer
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenRefreshView


class IsAdminOrSuperAdmin(permissions.BasePermission):
    """
    Custom permission to only allow admins and superadmins.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_admin() or request.user.is_superadmin())


class LoginView(APIView):
    """
    POST /api/login/ - JWT Authentication endpoint
    Accepts username and password, returns JWT tokens
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserTasksView(APIView):
    """
    GET /api/tasks - Fetch all tasks assigned to the logged-in user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        tasks = Task.objects.filter(assigned_to=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


class UpdateTaskView(APIView):
    """
    PUT /api/tasks/{id} - Update task status with completion report and worked hours
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self, task_id, user):
        return get_object_or_404(Task, id=task_id, assigned_to=user)
    
    def put(self, request, task_id):
        task = self.get_object(task_id, request.user)
        
        # If task is already completed, don't allow updates
        if task.status == 'completed':
            return Response(
                {'error': 'Cannot update a completed task'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TaskUpdateSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(TaskSerializer(task).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskReportView(APIView):
    """
    GET /api/tasks/{id}/report - View completion report for admins and superadmins
    """
    permission_classes = [IsAdminOrSuperAdmin]
    
    def get_object(self, task_id):
        return get_object_or_404(Task, id=task_id)
    
    def get(self, request, task_id):
        task = self.get_object(task_id)
        
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
    




  