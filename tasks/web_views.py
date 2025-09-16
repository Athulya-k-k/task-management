from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import User, Task
from .forms import UserCreationForm, TaskForm, TaskCompletionForm

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None and (user.is_admin() or user.is_superadmin()):
            auth_login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions')
    
    return render(request, 'admin/login.html')

@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('admin_login')

@login_required
def dashboard(request):
    if not (request.user.is_admin() or request.user.is_superadmin()):
        messages.error(request, 'Access denied')
        return redirect('admin_login')
    
    context = {
        'user_count': User.objects.filter(role='user').count(),
        'admin_count': User.objects.filter(role='admin').count(),
        'total_tasks': Task.objects.all().count(),
        'completed_tasks': Task.objects.filter(status='completed').count(),
    }
    
    if request.user.is_admin():
        # Admin can only see their own statistics
        context['user_count'] = User.objects.filter(assigned_admin=request.user).count()
        context['total_tasks'] = Task.objects.filter(created_by=request.user).count()
        context['completed_tasks'] = Task.objects.filter(created_by=request.user, status='completed').count()
    
    return render(request, 'admin/dashboard.html', context)

@login_required
def manage_users(request):
    if not request.user.is_superadmin():
        messages.error(request, 'Access denied')
        return redirect('admin_dashboard')
    
    users = User.objects.filter(role='user')
    admins = User.objects.filter(role='admin')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully')
            return redirect('manage_users')
    else:
        form = UserCreationForm()
    
    context = {
        'users': users,
        'admins': admins,
        'form': form,
    }
    return render(request, 'admin/manage_users.html', context)

@login_required
def delete_user(request, user_id):
    if not request.user.is_superadmin():
        messages.error(request, 'Access denied')
        return redirect('admin_dashboard')
    
    user = get_object_or_404(User, id=user_id)
    if user != request.user:
        user.delete()
        messages.success(request, 'User deleted successfully')
    else:
        messages.error(request, 'Cannot delete yourself')
    
    return redirect('manage_users')

@login_required
def assign_user_to_admin(request, user_id, admin_id):
    if not request.user.is_superadmin():
        messages.error(request, 'Access denied')
        return redirect('admin_dashboard')
    
    user = get_object_or_404(User, id=user_id, role='user')
    admin = get_object_or_404(User, id=admin_id, role='admin')
    
    user.assigned_admin = admin
    user.save()
    
    messages.success(request, f'User {user.username} assigned to admin {admin.username}')
    return redirect('manage_users')

@login_required
def manage_tasks(request):
    if not (request.user.is_admin() or request.user.is_superadmin()):
        messages.error(request, 'Access denied')
        return redirect('admin_dashboard')
    
    # Filter tasks based on user role
    if request.user.is_superadmin():
        tasks = Task.objects.all()
    else:
        # Admin can only see tasks they created
        tasks = Task.objects.filter(created_by=request.user)
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) | 
            Q(assigned_to__username__icontains=search)
        )
    
    # Status filter
    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, 'Task created successfully')
            return redirect('manage_tasks')
    else:
        form = TaskForm(user=request.user)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'search': search,
        'status_filter': status_filter,
        'status_choices': Task.STATUS_CHOICES,
    }
    return render(request, 'admin/manage_tasks.html', context)

@login_required
def view_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Permission check
    if request.user.is_admin() and task.created_by != request.user:
        messages.error(request, 'Access denied')
        return redirect('manage_tasks')
    
    return render(request, 'admin/view_task.html', {'task': task})

@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Permission check - only assigned user can complete
    if task.assigned_to != request.user:
        messages.error(request, 'You can only complete tasks assigned to you')
        return redirect('manage_tasks')
    
    if request.method == 'POST':
        form = TaskCompletionForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save(commit=False)
            task.status = 'completed'
            task.save()
            messages.success(request, 'Task completed successfully')
            return redirect('manage_tasks')
    else:
        form = TaskCompletionForm(instance=task)
    
    return render(request, 'admin/complete_task.html', {'task': task, 'form': form})

@login_required
def task_reports(request):
    if not (request.user.is_admin() or request.user.is_superadmin()):
        messages.error(request, 'Access denied')
        return redirect('admin_dashboard')
    
    # Filter completed tasks based on user role
    if request.user.is_superadmin():
        tasks = Task.objects.filter(status='completed')
    else:
        # Admin can only see reports for tasks they created
        tasks = Task.objects.filter(created_by=request.user, status='completed')
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) | 
            Q(assigned_to__username__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
    }
    return render(request, 'admin/task_reports.html', context)