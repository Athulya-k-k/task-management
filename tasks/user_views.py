from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import date
import json
from .models import User, Task
from .forms import TaskCompletionForm


def user_tasks(request):
    """
    Serve the user frontend for task management
    """
    return render(request, 'user/index.html')


@login_required
def user_dashboard(request):
    """
    User dashboard with task overview
    """
    if not request.user.is_user():
        messages.error(request, 'Access denied. This area is for users only.')
        return redirect('admin_login')
    
    user_tasks = Task.objects.filter(assigned_to=request.user)
    
    context = {
        'user': request.user,
        'total_tasks': user_tasks.count(),
        'pending_tasks': user_tasks.filter(status='pending').count(),
        'in_progress_tasks': user_tasks.filter(status='in_progress').count(),
        'completed_tasks': user_tasks.filter(status='completed').count(),
        'recent_tasks': user_tasks[:5],
        'today': date.today(),
    }
    
    return render(request, 'user/dashboard.html', context)


@login_required
def user_task_list(request):
    """
    Display all tasks assigned to the logged-in user with filtering options
    """
    if not request.user.is_user():
        messages.error(request, 'Access denied')
        return redirect('admin_login')
    
    tasks = Task.objects.filter(assigned_to=request.user)
    
    # Status filter
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['pending', 'in_progress', 'completed']:
        tasks = tasks.filter(status=status_filter)
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['title', '-title', 'due_date', '-due_date', 'status', '-status', 'created_at', '-created_at']:
        tasks = tasks.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(tasks, 6)  # 6 tasks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'status_choices': Task.STATUS_CHOICES,
    }
    
    return render(request, 'user/task_list.html', context)


@login_required
def user_task_detail(request, task_id):
    """
    Display detailed view of a specific task
    """
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    
    context = {
        'task': task,
        'today': date.today(),
        'can_start': task.status == 'pending',
        'can_complete': task.status in ['pending', 'in_progress'],
        'is_overdue': task.due_date < date.today() and task.status != 'completed',
    }
    
    return render(request, 'user/task_detail.html', context)


@login_required
@require_http_methods(["POST"])
def update_task_status(request, task_id):
    """
    Update task status (start task - pending to in_progress)
    """
    if not request.user.is_user():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status not in ['pending', 'in_progress', 'completed']:
            return JsonResponse({'error': 'Invalid status'}, status=400)
        
        # Only allow certain transitions
        if task.status == 'pending' and new_status == 'in_progress':
            task.status = new_status
            task.save()
            return JsonResponse({
                'success': True,
                'message': 'Task started successfully',
                'new_status': task.get_status_display()
            })
        elif task.status == 'in_progress' and new_status == 'pending':
            task.status = new_status
            task.save()
            return JsonResponse({
                'success': True,
                'message': 'Task moved back to pending',
                'new_status': task.get_status_display()
            })
        else:
            return JsonResponse({
                'error': 'Invalid status transition'
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def complete_task(request, task_id):
    """
    Handle task completion with report and worked hours
    """
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    
    if task.status == 'completed':
        messages.info(request, 'This task is already completed')
        return redirect('user_task_detail', task_id=task_id)
    
    if request.method == 'POST':
        form = TaskCompletionForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save(commit=False)
            task.status = 'completed'
            task.save()
            messages.success(request, 'Task completed successfully!')
            return redirect('user_task_detail', task_id=task_id)
    else:
        form = TaskCompletionForm(instance=task)
    
    context = {
        'task': task,
        'form': form,
    }
    
    return render(request, 'user/complete_task.html', context)


@login_required
@csrf_exempt
def complete_task_ajax(request, task_id):
    """
    AJAX endpoint for task completion
    """
    if not request.user.is_user():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    
    if task.status == 'completed':
        return JsonResponse({'error': 'Task is already completed'}, status=400)
    
    try:
        data = json.loads(request.body)
        completion_report = data.get('completion_report', '').strip()
        worked_hours = data.get('worked_hours')
        
        # Validation
        if not completion_report or len(completion_report) < 10:
            return JsonResponse({
                'error': 'Completion report must be at least 10 characters long'
            }, status=400)
        
        try:
            worked_hours = float(worked_hours)
            if worked_hours <= 0:
                return JsonResponse({
                    'error': 'Worked hours must be greater than 0'
                }, status=400)
        except (ValueError, TypeError):
            return JsonResponse({
                'error': 'Invalid worked hours value'
            }, status=400)
        
        # Update task
        task.status = 'completed'
        task.completion_report = completion_report
        task.worked_hours = worked_hours
        task.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Task completed successfully!',
            'task': {
                'id': task.id,
                'title': task.title,
                'status': task.get_status_display(),
                'worked_hours': float(task.worked_hours),
                'completion_report': task.completion_report,
                'updated_at': task.updated_at.isoformat()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def user_profile(request):
    """
    User profile page
    """
    if not request.user.is_user():
        messages.error(request, 'Access denied')
        return redirect('admin_login')
    
    user_tasks = Task.objects.filter(assigned_to=request.user)
    total_hours = sum(task.worked_hours or 0 for task in user_tasks if task.worked_hours)
    
    context = {
        'user': request.user,
        'total_tasks': user_tasks.count(),
        'completed_tasks': user_tasks.filter(status='completed').count(),
        'total_hours_worked': total_hours,
        'assigned_admin': request.user.assigned_admin,
    }
    
    return render(request, 'user/profile.html', context)


@login_required
def user_task_history(request):
    """
    Display completed tasks with reports
    """
    if not request.user.is_user():
        messages.error(request, 'Access denied')
        return redirect('admin_login')
    
    completed_tasks = Task.objects.filter(
        assigned_to=request.user,
        status='completed'
    ).order_by('-updated_at')
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        completed_tasks = completed_tasks.filter(
            Q(title__icontains=search) | 
            Q(completion_report__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(completed_tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    total_hours = sum(task.worked_hours or 0 for task in completed_tasks)
    avg_hours = total_hours / completed_tasks.count() if completed_tasks.count() > 0 else 0
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'total_completed': completed_tasks.count(),
        'total_hours_worked': total_hours,
        'average_hours_per_task': round(avg_hours, 2),
    }
    
    return render(request, 'user/task_history.html', context)


def user_login(request):
    """
    User login page (separate from admin login)
    """
    if request.user.is_authenticated and request.user.is_user():
        return redirect('user_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_user():
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('user_dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions')
    
    return render(request, 'user/login.html')


@login_required
def user_logout(request):
    """
    User logout
    """
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('user_login')


# API-like views for AJAX requests
@login_required
def get_task_stats(request):
    """
    Get user task statistics as JSON
    """
    if not request.user.is_user():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    tasks = Task.objects.filter(assigned_to=request.user)
    
    stats = {
        'total_tasks': tasks.count(),
        'pending_tasks': tasks.filter(status='pending').count(),
        'in_progress_tasks': tasks.filter(status='in_progress').count(),
        'completed_tasks': tasks.filter(status='completed').count(),
        'total_hours_worked': sum(task.worked_hours or 0 for task in tasks),
        'overdue_tasks': tasks.filter(
            due_date__lt=date.today(),
            status__in=['pending', 'in_progress']
        ).count(),
    }
    
    return JsonResponse(stats)


@login_required
def get_upcoming_tasks(request):
    """
    Get upcoming tasks (next 7 days) as JSON
    """
    if not request.user.is_user():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    from datetime import timedelta
    
    upcoming_tasks = Task.objects.filter(
        assigned_to=request.user,
        due_date__gte=date.today(),
        due_date__lte=date.today() + timedelta(days=7),
        status__in=['pending', 'in_progress']
    ).order_by('due_date')
    
    tasks_data = []
    for task in upcoming_tasks:
        tasks_data.append({
            'id': task.id,
            'title': task.title,
            'due_date': task.due_date.isoformat(),
            'status': task.status,
            'status_display': task.get_status_display(),
        })
    
    return JsonResponse({'tasks': tasks_data})