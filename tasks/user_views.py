# Create tasks/user_views.py
from django.shortcuts import render

def user_tasks(request):
    """
    Serve the user frontend for task management
    """
    return render(request, 'user/index.html')


