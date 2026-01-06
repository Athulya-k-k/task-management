from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Task

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include username and password')

class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'assigned_to', 'assigned_to_name', 
                 'created_by', 'created_by_name', 'due_date', 'status', 
                 'completion_report', 'worked_hours', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']



class TaskUpdateSerializer(serializers.ModelSerializer):
    completion_report = serializers.CharField(
        required=False,
        allow_blank=True
    )
    worked_hours = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Task
        fields = ['status', 'completion_report', 'worked_hours']

    def validate(self, attrs):
        status = attrs.get(
            'status',
            self.instance.status if self.instance else None
        )

        # Only validate when changing TO completed status
        if status == 'completed':
            completion_report = attrs.get(
                'completion_report',
                self.instance.completion_report if self.instance else None
            )
            worked_hours = attrs.get(
                'worked_hours',
                self.instance.worked_hours if self.instance else None
            )

            if not completion_report:
                raise serializers.ValidationError({
                    'completion_report':
                        'Completion report is required when marking task as completed'
                })

            if worked_hours is None:
                raise serializers.ValidationError({
                    'worked_hours':
                        'Worked hours is required when marking task as completed'
                })

        return attrs




class TaskReportSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    assigned_to_email = serializers.CharField(source='assigned_to.email', read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'assigned_to_name', 'assigned_to_email',
                 'due_date', 'status', 'completion_report', 'worked_hours', 
                 'created_at', 'updated_at']