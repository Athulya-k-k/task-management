from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import date
from .models import User, Task
from .forms import UserCreationForm, UserEditForm, TaskForm, TaskEditForm, TaskCompletionForm

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
        'today': date.today(),
    }
    
    if request.user.is_admin():
        # Admin can only see their own statistics
        context['user_count'] = User.objects.filter(assigned_admin=request.user).count()
        context['total_tasks'] = Task.objects.filter(created_by=request.user).count()
        context['completed_tasks'] = Task.objects.filter(created_by=request.user, status='completed').count()
    
    return render(request, 'admin/dashboard.html', context)

# USER CRUD OPERATIONS
@login_required
def manage_users(request):
    if not request.user.is_superadmin():
        messages.error(request, 'Access denied')
        return redirect('admin_dashboard')
    
    users = User.objects.filter(role='user')
    admins = User.objects.filter(role='admin')
    superadmins = User.objects.filter(role='superadmin')
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        users = users.filter(
            Q(username__icontains=search) | 
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
        admins = admins.filter(
            Q(username__icontains=search) | 
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    context = {
        'users': users,
        'admins': admins,
        'superadmins': superadmins,
        'search': search,
    }
    return render(request, 'admin/manage_users.html', context)

@login_required
def create_user(request):
    if not request.user.is_superadmin():
        messages.error(request, 'Access denied')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST, current_user=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully')
            return redirect('manage_users')
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserCreationForm(current_user=request.user)
    
    context = {
        'form': form,
        'page_title': 'Create New User',
        'submit_text': 'Create User',
    }
    return render(request, 'admin/user_form.html', context)

@login_required
def view_user(request, user_id):
    if not request.user.is_superadmin():
        messages.error(request, 'Access denied')
        return redirect('admin_dashboard')
    
    user_obj = get_object_or_404(User, id=user_id)
    
    # Get user's tasks if they are a regular user
    tasks = Task.objects.filter(assigned_to=user_obj) if user_obj.role == 'user' else None
    created_tasks = Task.objects.filter(created_by=user_obj) if user_obj.role in ['admin', 'superadmin'] else None
    
    context = {
        'user_obj': user_obj,
        'tasks': tasks,
        'created_tasks': created_tasks,
    }
    return render(request, 'admin/view_user.html', context)

@login_required
def edit_user(request, user_id):
    if not request.user.is_superadmin():
        messages.error(request, 'Access denied')
        return redirect('admin_dashboard')
    
    user_obj = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_obj, current_user=request.user)
        if form.is_valid():
            user_obj = form.save()
            messages.success(request, f'User {user_obj.username} updated successfully')
            return redirect('manage_users')
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserEditForm(instance=user_obj, current_user=request.user)
    
    context = {
        'form': form,
        'user_obj': user_obj,
        'page_title': f'Edit User: {user_obj.username}',
        'submit_text': 'Update User',
    }
    return render(request, 'admin/user_form.html', context)

@login_required
def delete_user(request, user_id):
    if not request.user.is_superadmin():
        messages.error(request, 'Access denied')
        return redirect('admin_dashboard')
    
    user_obj = get_object_or_404(User, id=user_id)
    
    if user_obj == request.user:
        messages.error(request, 'Cannot delete yourself')
        return redirect('manage_users')
    
    if request.method == 'POST':
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f'User {username} deleted successfully')
        return redirect('manage_users')
    
    context = {
        'user_obj': user_obj,
    }
    return render(request, 'admin/delete_user.html', context)

@login_required
def assign_user_to_admin(request, user_id, admin_id):
    if not request.user.is_superadmin():
        messages.error(request, 'Access denied')
        return redirect('admin_dashboard')
    
    user_obj = get_object_or_404(User, id=user_id, role='user')
    admin = get_object_or_404(User, id=admin_id, role='admin')
    
    user_obj.assigned_admin = admin
    user_obj.save()
    
    messages.success(request, f'User {user_obj.username} assigned to admin {admin.username}')
    return redirect('manage_users')

# TASK CRUD OPERATIONS
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
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'status_choices': Task.STATUS_CHOICES,
        'today': date.today(),
    }
    return render(request, 'admin/manage_tasks.html', context)

@login_required
def create_task(request):
    if not (request.user.is_admin() or request.user.is_superadmin()):
        messages.error(request, 'Access denied')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, 'Task created successfully')
            return redirect('manage_tasks')
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = TaskForm(user=request.user)
    
    context = {
        'form': form,
        'page_title': 'Create New Task',
        'submit_text': 'Create Task',
    }
    return render(request, 'admin/task_form.html', context)

@login_required
def view_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Permission check
    if request.user.is_admin() and task.created_by != request.user:
        messages.error(request, 'Access denied')
        return redirect('manage_tasks')
    
    context = {
        'task': task,
        'today': date.today(),
    }
    return render(request, 'admin/view_task.html', context)

@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Permission check
    if request.user.is_admin() and task.created_by != request.user:
        messages.error(request, 'Access denied')
        return redirect('manage_tasks')
    
    if request.method == 'POST':
        form = TaskEditForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Task "{task.title}" updated successfully')
            return redirect('view_task', task_id=task.id)
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = TaskEditForm(instance=task, user=request.user)
    
    context = {
        'form': form,
        'task': task,
        'page_title': f'Edit Task: {task.title}',
        'submit_text': 'Update Task',
    }
    return render(request, 'admin/task_form.html', context)

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Permission check
    if request.user.is_admin() and task.created_by != request.user:
        messages.error(request, 'Access denied')
        return redirect('manage_tasks')
    
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'Task "{task_title}" deleted successfully')
        return redirect('manage_tasks')
    
    context = {
        'task': task,
    }
    return render(request, 'admin/delete_task.html', context)

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
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
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