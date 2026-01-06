from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.generic import View, ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse_lazy
from datetime import date
from .models import User, Task
from .forms import UserCreationForm, UserEditForm, TaskForm, TaskEditForm
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test


# ===========================
# PERMISSION MIXINS
# ===========================

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require admin or superadmin permissions"""
    
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_admin() or user.is_superadmin())
    
    def handle_no_permission(self):
        messages.error(self.request, 'Access denied')
        return redirect('admin_login')


class SuperAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require superadmin permissions"""
    
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.is_superadmin()
    
    def handle_no_permission(self):
        messages.error(self.request, 'Access denied')
        return redirect('admin_dashboard')


class TaskPermissionMixin(LoginRequiredMixin):
    """Mixin for task permissions"""
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin() or request.user.is_superadmin()):
            messages.error(request, 'Access denied')
            return redirect('admin_dashboard')
        
        if 'task_id' in kwargs or 'pk' in kwargs:
            task_id = kwargs.get('task_id') or kwargs.get('pk')
            task = get_object_or_404(Task, id=task_id)
            
            # Check if admin can access this task
            if request.user.is_admin() and task.created_by != request.user:
                messages.error(request, 'Access denied')
                return redirect('manage_tasks')
        
        return super().dispatch(request, *args, **kwargs)


# ===========================
# AUTHENTICATION VIEWS
# ===========================

class LoginView(View):
    """Admin/SuperAdmin login page"""
    
    def get(self, request):
        if request.user.is_authenticated and (request.user.is_admin() or request.user.is_superadmin()):
            return redirect('admin_dashboard')
        return render(request, 'admin/login.html')
    
    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None and (user.is_admin() or user.is_superadmin()):
            auth_login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions')
        
        return render(request, 'admin/login.html')


class LogoutView(LoginRequiredMixin, View):
    """Logout admin/superadmin"""
    
    def get(self, request):
        auth_logout(request)
        return redirect('admin_login')


class DashboardView(AdminRequiredMixin, View):
    """Admin panel dashboard"""
    
    def get(self, request):
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


# ===========================
# USER MANAGEMENT (SuperAdmin Only)
# ===========================

class ManageUsersView(SuperAdminRequiredMixin, View):
    """View all users, admins, and superadmins"""
    
    def get(self, request):
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


class CreateUserView(SuperAdminRequiredMixin, View):
    """Create a new user"""
    
    def get(self, request):
        form = UserCreationForm(current_user=request.user)
        context = {
            'form': form,
            'page_title': 'Create New User',
            'submit_text': 'Create User',
        }
        return render(request, 'admin/user_form.html', context)
    
    def post(self, request):
        form = UserCreationForm(request.POST, current_user=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully')
            return redirect('manage_users')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        
        context = {
            'form': form,
            'page_title': 'Create New User',
            'submit_text': 'Create User',
        }
        return render(request, 'admin/user_form.html', context)


class ViewUserView(SuperAdminRequiredMixin, DetailView):
    """View user details"""
    model = User
    template_name = 'admin/view_user.html'
    context_object_name = 'user_obj'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_obj = self.get_object()
        
        # Get user's tasks if they are a regular user
        if user_obj.role == 'user':
            context['tasks'] = Task.objects.filter(assigned_to=user_obj)
        else:
            context['tasks'] = None
            
        # Get tasks created by admin/superadmin
        if user_obj.role in ['admin', 'superadmin']:
            context['created_tasks'] = Task.objects.filter(created_by=user_obj)
        else:
            context['created_tasks'] = None
            
        return context


class EditUserView(SuperAdminRequiredMixin, View):
    """Edit existing user"""
    
    def get(self, request, user_id):
        user_obj = get_object_or_404(User, id=user_id)
        form = UserEditForm(instance=user_obj, current_user=request.user)
        context = {
            'form': form,
            'user_obj': user_obj,
            'page_title': f'Edit User: {user_obj.username}',
            'submit_text': 'Update User',
        }
        return render(request, 'admin/user_form.html', context)
    
    def post(self, request, user_id):
        user_obj = get_object_or_404(User, id=user_id)
        form = UserEditForm(request.POST, instance=user_obj, current_user=request.user)
        
        if form.is_valid():
            user_obj = form.save()
            messages.success(request, f'User {user_obj.username} updated successfully')
            return redirect('manage_users')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        
        context = {
            'form': form,
            'user_obj': user_obj,
            'page_title': f'Edit User: {user_obj.username}',
            'submit_text': 'Update User',
        }
        return render(request, 'admin/user_form.html', context)


class DeleteUserView(SuperAdminRequiredMixin, View):
    """Delete a user"""
    
    def get(self, request, user_id):
        user_obj = get_object_or_404(User, id=user_id)
        
        if user_obj == request.user:
            messages.error(request, 'Cannot delete yourself')
            return redirect('manage_users')
        
        context = {'user_obj': user_obj}
        return render(request, 'admin/delete_user.html', context)
    
    def post(self, request, user_id):
        user_obj = get_object_or_404(User, id=user_id)
        
        if user_obj == request.user:
            messages.error(request, 'Cannot delete yourself')
            return redirect('manage_users')
        
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f'User {username} deleted successfully')
        return redirect('manage_users')


class AssignUserToAdminView(SuperAdminRequiredMixin, View):
    """Assign a user to an admin"""
    
    def get(self, request, user_id, admin_id):
        user_obj = get_object_or_404(User, id=user_id, role='user')
        admin = get_object_or_404(User, id=admin_id, role='admin')
        
        user_obj.assigned_admin = admin
        user_obj.save()
        
        messages.success(request, f'User {user_obj.username} assigned to admin {admin.username}')
        return redirect('manage_users')


# ===========================
# TASK MANAGEMENT
# ===========================

class ManageTasksView(TaskPermissionMixin, View):
    """View and manage tasks"""
    
    def get(self, request):
        form = TaskForm(user=request.user)
        
        # Filter tasks based on role
        if request.user.is_superadmin():
            tasks = Task.objects.all()
        else:
            tasks = Task.objects.filter(created_by=request.user)
        
        # Search & filter
        search = request.GET.get('search')
        if search:
            tasks = tasks.filter(
                Q(title__icontains=search) |
                Q(assigned_to__username__icontains=search)
            )
        
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
            'form': form,
        }
        return render(request, 'admin/manage_tasks.html', context)
    
    def post(self, request):
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, "Task created successfully.")
            return redirect('manage_tasks')
        else:
            messages.error(request, "Please correct the errors below.")
        
        # If form is invalid, re-render the page with errors
        # Filter tasks based on role
        if request.user.is_superadmin():
            tasks = Task.objects.all()
        else:
            tasks = Task.objects.filter(created_by=request.user)
        
        # Pagination
        paginator = Paginator(tasks, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'search': request.GET.get('search', ''),
            'status_filter': request.GET.get('status', ''),
            'status_choices': Task.STATUS_CHOICES,
            'today': date.today(),
            'form': form,
        }
        return render(request, 'admin/manage_tasks.html', context)


class CreateTaskView(TaskPermissionMixin, View):
    """Create a new task"""
    
    def get(self, request):
        form = TaskForm(user=request.user)
        context = {
            'form': form,
            'page_title': 'Create New Task',
            'submit_text': 'Create Task',
        }
        return render(request, 'admin/task_form.html', context)
    
    def post(self, request):
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, 'Task created successfully')
            return redirect('manage_tasks')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        
        context = {
            'form': form,
            'page_title': 'Create New Task',
            'submit_text': 'Create Task',
        }
        return render(request, 'admin/task_form.html', context)


class ViewTaskView(TaskPermissionMixin, DetailView):
    """View task details"""
    model = Task
    template_name = 'admin/view_task.html'
    context_object_name = 'task'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = date.today()
        return context


from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib import messages

from .models import Task
from .forms import TaskEditForm


class EditTaskView(TaskPermissionMixin, View):
    """Edit existing task"""

    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        form = TaskEditForm(instance=task, user=request.user)

        context = {
            'form': form,
            'task': task,
            'page_title': f'Edit Task: {task.title}',
            'submit_text': 'Update Task',
        }
        return render(request, 'admin/task_form.html', context)

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        form = TaskEditForm(request.POST, instance=task, user=request.user)

        if form.is_valid():
            task = form.save()
            messages.success(
                request,
                f'Task "{task.title}" updated successfully'
            )
            return redirect('view_task', pk=task.pk)

        # Form errors
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')

        context = {
            'form': form,
            'task': task,
            'page_title': f'Edit Task: {task.title}',
            'submit_text': 'Update Task',
        }
        return render(request, 'admin/task_form.html', context)


class DeleteTaskView(TaskPermissionMixin, View):
    """Delete a task (confirmation + delete)"""

    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        context = {
            'task': task
        }
        return render(request, 'admin/delete_task.html', context)

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        task_title = task.title
        task.delete()

        messages.success(
            request,
            f'Task "{task_title}" deleted successfully'
        )
        return redirect('manage_tasks')

# ===========================
# TASK REPORTS
# ===========================

class TaskReportsView(AdminRequiredMixin, View):
    """View completion reports for completed tasks"""
    
    def get(self, request):
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