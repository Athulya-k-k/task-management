from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate
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
from .serializers import UserSerializer
from .decorators import jwt_required

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


# -----------------------------
# LOGIN / LOGOUT
# -----------------------------
@csrf_exempt
def api_login(request):
    if request.method == "GET":
        return render(request, "user/login.html")

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")
        except:
            return JsonResponse({"detail": "Invalid JSON"}, status=400)

        user = authenticate(username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            response = JsonResponse({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data
            })
            # Set JWT in cookie for template views
            response.set_cookie(
                key='jwt',
                value=str(refresh.access_token),
                httponly=True,
                samesite='Lax'
            )
            return response
        else:
            return JsonResponse({"detail": "Invalid credentials"}, status=401)
    
    return JsonResponse({"detail": "Method not allowed"}, status=405)


def api_logout(request):
    response = redirect('/api/login/')
    response.delete_cookie('jwt')
    return response


# -----------------------------
# DASHBOARD / SPA
# -----------------------------
def user_tasks(request):
    """Serve the main user SPA"""
    return render(request, 'user/index.html')


@jwt_required
def user_dashboard(request):
    return render(request, "user/dashboard.html")


# -----------------------------
# TASK VIEWS
# -----------------------------
@jwt_required
def user_task_list(request):
    """List tasks with filtering, search, sort, pagination"""
    if not request.user.is_user():
        messages.error(request, 'Access denied')
        return redirect('/api/login/')
    
    tasks = Task.objects.filter(assigned_to=request.user)

    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter in ['pending', 'in_progress', 'completed']:
        tasks = tasks.filter(status=status_filter)

    # Search
    search = request.GET.get('search')
    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )

    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['title','-title','due_date','-due_date','status','-status','created_at','-created_at']:
        tasks = tasks.order_by(sort_by)

    # Pagination
    paginator = Paginator(tasks, 6)
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


@jwt_required
def user_task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    context = {
        'task': task,
        'today': date.today(),
        'can_start': task.status == 'pending',
        'can_complete': task.status in ['pending', 'in_progress'],
        'is_overdue': task.due_date < date.today() and task.status != 'completed',
    }
    return render(request, 'user/task_detail.html', context)


@jwt_required
@require_http_methods(["POST"])
def update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        if new_status not in ['pending', 'in_progress', 'completed']:
            return JsonResponse({'error': 'Invalid status'}, status=400)
        # Status transitions
        if task.status == 'pending' and new_status == 'in_progress':
            task.status = new_status
            task.save()
        elif task.status == 'in_progress' and new_status == 'pending':
            task.status = new_status
            task.save()
        else:
            return JsonResponse({'error': 'Invalid status transition'}, status=400)
        return JsonResponse({'success': True, 'new_status': task.get_status_display()})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@jwt_required
def complete_task(request, task_id):
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

    context = {'task': task, 'form': form}
    return render(request, 'user/complete_task.html', context)


@jwt_required
@csrf_exempt
def complete_task_ajax(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    if task.status == 'completed':
        return JsonResponse({'error': 'Task is already completed'}, status=400)

    try:
        data = json.loads(request.body)
        completion_report = data.get('completion_report', '').strip()
        worked_hours = data.get('worked_hours')

        if not completion_report or len(completion_report) < 10:
            return JsonResponse({'error': 'Completion report must be at least 10 characters'}, status=400)

        try:
            worked_hours = float(worked_hours)
            if worked_hours <= 0:
                return JsonResponse({'error': 'Worked hours must be > 0'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid worked hours'}, status=400)

        task.status = 'completed'
        task.completion_report = completion_report
        task.worked_hours = worked_hours
        task.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# -----------------------------
# USER PROFILE
# -----------------------------
@jwt_required
def user_profile(request):
    if not request.user.is_user():
        messages.error(request, 'Access denied')
        return redirect('/api/login/')

    user_tasks = Task.objects.filter(assigned_to=request.user)
    total_hours = sum(task.worked_hours or 0 for task in user_tasks)

    context = {
        'user': request.user,
        'total_tasks': user_tasks.count(),
        'completed_tasks': user_tasks.filter(status='completed').count(),
        'total_hours_worked': total_hours,
        'assigned_admin': request.user.assigned_admin,
    }
    return render(request, 'user/profile.html', context)


@jwt_required
def user_task_history(request):
    if not request.user.is_user():
        messages.error(request, 'Access denied')
        return redirect('/api/login/')

    completed_tasks = Task.objects.filter(
        assigned_to=request.user, status='completed'
    ).order_by('-updated_at')

    # Search
    search = request.GET.get('search')
    if search:
        completed_tasks = completed_tasks.filter(
            Q(title__icontains=search) | Q(completion_report__icontains=search)
        )

    paginator = Paginator(completed_tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

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


# -----------------------------
# AJAX STATISTICS
# -----------------------------
@jwt_required
def get_task_stats(request):
    if not request.user.is_user():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    tasks = Task.objects.filter(assigned_to=request.user)
    stats = {
        'total_tasks': tasks.count(),
        'pending_tasks': tasks.filter(status='pending').count(),
        'in_progress_tasks': tasks.filter(status='in_progress').count(),
        'completed_tasks': tasks.filter(status='completed').count(),
        'total_hours_worked': sum(task.worked_hours or 0 for task in tasks),
        'overdue_tasks': tasks.filter(due_date__lt=date.today(), status__in=['pending','in_progress']).count(),
    }
    return JsonResponse(stats)


@jwt_required
def get_upcoming_tasks(request):
    from datetime import timedelta
    tasks = Task.objects.filter(
        assigned_to=request.user,
        due_date__gte=date.today(),
        due_date__lte=date.today() + timedelta(days=7),
        status__in=['pending','in_progress']
    ).order_by('due_date')

    tasks_data = []
    for task in tasks:
        tasks_data.append({
            'id': task.id,
            'title': task.title,
            'due_date': task.due_date.isoformat(),
            'status': task.status,
            'status_display': task.get_status_display()
        })
    return JsonResponse({'tasks': tasks_data})
