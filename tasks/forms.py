from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from .models import User, Task

class UserCreationForm(BaseUserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    # Use the same choices as the model
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    assigned_admin = forms.ModelChoiceField(
        queryset=User.objects.filter(role='admin'), 
        required=False,
        help_text="Only required for users"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role', 'assigned_admin')

    def __init__(self, *args, **kwargs):
        # Get the current user to determine available role choices
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Apply CSS classes
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['role'].widget.attrs.update({'class': 'form-control'})
        self.fields['assigned_admin'].widget.attrs.update({'class': 'form-control'})

        # Limit role choices based on current user
        if current_user:
            if current_user.is_superadmin():
                # SuperAdmin can create all types of users
                self.fields['role'].choices = User.ROLE_CHOICES
            elif current_user.is_admin():
                # Admin can only create regular users
                self.fields['role'].choices = [('user', 'User')]
            else:
                # Regular users cannot create accounts
                self.fields['role'].choices = []

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        assigned_admin = cleaned_data.get('assigned_admin')

        if role == 'user' and not assigned_admin:
            raise forms.ValidationError("Users must be assigned to an admin")
        
        if role in ['admin', 'superadmin'] and assigned_admin:
            cleaned_data['assigned_admin'] = None

        return cleaned_data

class UserEditForm(forms.ModelForm):
    """Form for editing existing users"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    assigned_admin = forms.ModelChoiceField(
        queryset=User.objects.filter(role='admin'), 
        required=False,
        help_text="Only required for users"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'assigned_admin', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'assigned_admin': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Limit role choices based on current user
        if current_user:
            if current_user.is_superadmin():
                # SuperAdmin can edit all types of users
                self.fields['role'].choices = User.ROLE_CHOICES
            elif current_user.is_admin():
                # Admin can only edit regular users
                self.fields['role'].choices = [('user', 'User')]
            else:
                # Regular users cannot edit accounts
                self.fields['role'].choices = []

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        assigned_admin = cleaned_data.get('assigned_admin')

        if role == 'user' and not assigned_admin:
            raise forms.ValidationError("Users must be assigned to an admin")
        
        if role in ['admin', 'superadmin'] and assigned_admin:
            cleaned_data['assigned_admin'] = None

        return cleaned_data

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'due_date', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            if user.is_superadmin():
                # SuperAdmin can assign tasks to any user
                self.fields['assigned_to'].queryset = User.objects.filter(role='user')
            elif user.is_admin():
                # Admin can only assign tasks to their assigned users
                self.fields['assigned_to'].queryset = User.objects.filter(assigned_admin=user)

class TaskEditForm(forms.ModelForm):
    """Form for editing existing tasks"""
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'due_date', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            if user.is_superadmin():
                # SuperAdmin can assign tasks to any user
                self.fields['assigned_to'].queryset = User.objects.filter(role='user')
            elif user.is_admin():
                # Admin can only assign tasks to their assigned users
                self.fields['assigned_to'].queryset = User.objects.filter(assigned_admin=user)


  