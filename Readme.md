Task Management System
A comprehensive Django-based task management system with role-based access control, featuring separate interfaces for administrators and users.
Features
🔐 Role-Based Access Control

SuperAdmin: Full system access, can manage all users and tasks
Admin: Can create and manage regular users and their tasks
User: Can view and complete assigned tasks

📋 Task Management

Create, edit, and delete tasks
Task status tracking (Pending, In Progress, Completed)
Due date management with overdue notifications
Task completion reports with worked hours tracking
Search and filtering capabilities

👥 User Management

User creation and management by SuperAdmins
Admin assignment for regular users
User profile management
Active/inactive user status control

📊 Dashboard & Analytics

Task statistics and completion rates
Progress tracking and reporting
Task history and analytics
Overdue task notifications

🔌 API Integration

RESTful API endpoints
JWT token authentication
Mobile-friendly API responses
Secure authentication system

Tech Stack

Backend: Django 4.x
Database: SQLite (default) / PostgreSQL / MySQL
Authentication: JWT (JSON Web Tokens)
API: Django REST Framework
Frontend: HTML, CSS, JavaScript (SPA components)
Styling: Bootstrap

Installation
Prerequisites

Python 3.8+
pip
Virtual environment (recommended)

Setup

Clone the repository

bashgit clone <repository-url>
cd task-management-system

Create virtual environment

bashpython -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies

bashpip install -r requirements.txt



Run migrations

bashpython manage.py makemigrations
python manage.py migrate

Create superuser

bashpython manage.py createsuperuser

create superadmin

python manage.py create_superadmin --username=superadmin --email=admin@company.com --password=securepassword123

Run the development server

bashpython manage.py runserver
The application will be available at http://localhost:8000
Usage
Admin Interface
Access URLs

SuperAdmin/Admin Login: /admin/login/,admin-panel/login/
Admin Dashboard: /admin/
User Management: /admin/users/
Task Management: /admin/tasks/
Reports: /admin/reports/

Key Features

User Management: Create, edit, delete users and assign them to admins
Task Creation: Create and assign tasks to users with due dates
Task Monitoring: Track task progress and completion status
Reports: View completion reports with worked hours

User Interface
Access URLs

User Login: /api/login/
User Dashboard: /user/dashboard/
Task List: /user/tasks/
Task History: /user/history/
User Profile: /user/profile/

Key Features

Task Dashboard: View assigned tasks and statistics
Task Management: Update task status and complete tasks
Completion Reports: Submit detailed completion reports with hours worked
Profile: View personal information and task statistics

API Endpoints
Authentication
POST /api/login/          # User login
POST /api/token/refresh/       # Refresh JWT token
POST /user/api/logout/         # User logout
Tasks
GET    /api/tasks/             # Get user's tasks
PUT    /api/tasks/{id}/        # Update task
GET    /api/tasks/{id}/report/ # Get task report (Admin only)
User Roles & Permissions
SuperAdmin

✅ Full system access
✅ Create/manage all users (including admins)
✅ View all tasks and reports
✅ System configuration

Admin

✅ Create/manage regular users
✅ Create/assign tasks to their users
✅ View reports for their created tasks
❌ Cannot manage other admins or superadmins

User

✅ View assigned tasks
✅ Update task status (pending ↔ in progress)
✅ Complete tasks with reports
✅ View task history and personal stats
❌ Cannot create tasks or manage other users

API Authentication
The system uses JWT (JSON Web Tokens) for API authentication:

Login to get access and refresh tokens
Include access token in API requests:

   Authorization: Bearer <access-token>

Refresh tokens when they expire using the refresh endpoint

Database Schema
Models Overview
User Model (Custom)

Extends Django's AbstractUser
Additional fields: role, assigned_admin
Role choices: user, admin, superadmin

Task Model

Fields: title, description, assigned_to, created_by, due_date, status
Completion fields: completion_report, worked_hours
Timestamps: created_at, updated_at

Development
Project Structure
tasks/
├── admin.py          # Django admin configuration
├── api_urls.py       # API URL routing
├── api_views.py      # API view handlers
├── decorators.py     # Custom decorators (JWT)
├── forms.py          # Django forms
├── models.py         # Database models
├── serializers.py    # DRF serializers
├── user_urls.py      # User interface URLs
├── user_views.py     # User interface views
├── web_urls.py       # Admin interface URLs
├── web_views.py      # Admin interface views
└── templates/        # HTML templates
Key Components

Models (models.py)

Custom User model with role-based permissions
Task model with status tracking and completion details


Views

web_views.py: Admin interface views
user_views.py: User interface views
api_views.py: REST API endpoints


Forms (forms.py)

User creation and editing forms
Task management forms
Task completion forms with validation


Authentication

JWT-based API authentication
Custom decorators for template views
Role-based permission classes



Contributing

Fork the repository
Create a feature branch (git checkout -b feature/amazing-feature)
Commit your changes (git commit -m 'Add amazing feature')
Push to the branch (git push origin feature/amazing-feature)
Open a Pull Request

Testing
Run the test suite:
bashpython manage.py test
Deployment
Production Settings

Environment Variables

Set DEBUG=False
Configure SECRET_KEY
Set database credentials
Configure ALLOWED_HOSTS


Database Migration

bash   python manage.py migrate --settings=myproject.settings.production

Static Files

bash   python manage.py collectstatic
Docker Deployment
dockerfile# Example Dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "myproject.wsgi:application"]
Security Features

✅ JWT token authentication
✅ Role-based access control
✅ CSRF protection
✅ SQL injection prevention (Django ORM)
✅ XSS protection
✅ Secure password hashing

Troubleshooting
Common Issues

Migration Errors

bash   python manage.py makemigrations tasks
   python manage.py migrate

JWT Token Issues

Check token expiration
Verify token format in Authorization header
Ensure user is active


Permission Denied

Verify user role and permissions
Check assigned_admin relationships
Ensure proper authentication



License
This project is licensed under the MIT License - see the LICENSE file for details.
Support
For support and questions:

Create an issue in the repository
Check the documentation
Review the code comments for implementation details


Version: 1.0.0
Last Updated: September 2025