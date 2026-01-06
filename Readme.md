# Task Management System

A comprehensive Django-based task management system with role-based access control, featuring three user roles: SuperAdmin, Admin, and User. The system provides both a web-based admin panel and RESTful API endpoints.

## Features

### Role-Based Access Control
- **SuperAdmin**: Full system access, can manage all users, admins, and tasks
- **Admin**: Can create tasks, assign and track tasks for their assigned users
- **User**: Can view assigned tasks and submit completion reports via API


### REST API
- JWT-based authentication
- Task retrieval for assigned users
- Task status updates with completion reports
- Secure endpoints with permission checks

## Technology Stack

- **Backend**: Django 4.2.7
- **Database**: SQLite 
- **API**: Django REST Framework
- **Authentication**: JWT (JSON Web Tokens)
- **Python**: 3.8+

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
```bash
git clone <repository-url>
cd task_management
```

2. **Create and activate virtual environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Apply database migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Create a superadmin user**
```bash
python manage.py createsuperuser
```
Follow the prompts to create your first superadmin account. Make sure to set the role to 'superadmin' in the admin interface or database.

6. **Run the development server**
```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Usage

### superadmin and admin interface

Access the superadmin and admin panel at: `http://127.0.0.1:8000/admin-panel/`

**Default Routes:**
- Login: `/admin-panel/login/`
- Dashboard: `/admin-panel/`
- Manage Users: `/admin-panel/users/`
- Manage Tasks: `/admin-panel/tasks/`
- Task Reports: `/admin-panel/reports/`

### REST API Endpoints

**Base URL**: `http://127.0.0.1:8000/api/`

#### Authentication
```http
POST /api/login/
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}

Response:
{
    "refresh": "refresh_token",
    "access": "access_token",
    "user": {
        "id": 1,
        "username": "username",
        "email": "user@example.com",
        "first_name": "First",
        "last_name": "Last",
        "role": "user"
    }
}
```

#### Get User Tasks
```http
GET /api/tasks/
Authorization: Bearer <access_token>

Response:
[
    {
        "id": 1,
        "title": "Task Title",
        "description": "Task Description",
        "assigned_to": 2,
        "assigned_to_name": "username",
        "created_by": 1,
        "created_by_name": "admin",
        "due_date": "2025-01-15",
        "status": "pending",
        "completion_report": null,
        "worked_hours": null,
        "created_at": "2025-01-06T10:00:00Z",
        "updated_at": "2025-01-06T10:00:00Z"
    }
]
```

#### Update Task Status
```http
PUT /api/tasks/{task_id}/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "status": "completed",
    "completion_report": "Task completed successfully. Details...",
    "worked_hours": "8.50"
}

Response:
{
    "id": 1,
    "title": "Task Title",
    "status": "completed",
    "completion_report": "Task completed successfully. Details...",
    "worked_hours": "8.50",
    ...
}
```

#### View Task Report (Admin/SuperAdmin only)
```http
GET /api/tasks/{task_id}/report/
Authorization: Bearer <access_token>

Response:
{
    "id": 1,
    "title": "Task Title",
    "description": "Task Description",
    "assigned_to_name": "username",
    "assigned_to_email": "user@example.com",
    "due_date": "2025-01-15",
    "status": "completed",
    "completion_report": "Task completed successfully...",
    "worked_hours": "8.50",
    "created_at": "2025-01-06T10:00:00Z",
    "updated_at": "2025-01-07T18:30:00Z"
}
```

#### Token Refresh
```http
POST /api/token/refresh/
Content-Type: application/json

{
    "refresh": "refresh_token"
}

Response:
{
    "access": "new_access_token"
}
```

## Project Structure

```
task_management/
├── task_management/          # Project settings
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL configuration
│   └── wsgi.py              # WSGI configuration
├── tasks/                    # Main application
│   ├── models.py            # User and Task models
│   ├── views.py             # (unused)
│   ├── web_views.py         # Web admin panel views
│   ├── api_views.py         # REST API views
│   ├── forms.py             # Django forms
│   ├── serializers.py       # DRF serializers
│   ├── web_urls.py          # Admin panel URLs
│   ├── api_urls.py          # API URLs
│   └── admin.py             # Django admin configuration
├── templates/
│   └── admin/               # Admin panel templates
│       ├── base.html        # Base template
│       ├── dashboard.html   # Dashboard
│       ├── manage_users.html
│       ├── manage_tasks.html
│       └── ...
├── manage.py                # Django management script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

