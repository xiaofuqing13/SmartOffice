"""Serializers for the users app."""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Company, Department, Contact
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserSimpleSerializer(serializers.ModelSerializer):
    """简单的用户信息序列化器，用于列表展示和关联引用"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'avatar', 'position', 'department']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'phone', 'avatar', 'position', 'department', 'company', 'bio']
        read_only_fields = ['id', 'email']


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for the User model."""
    department_name = serializers.CharField(source='department.name', read_only=True, allow_null=True)
    company_name = serializers.CharField(source='company.name', read_only=True, allow_null=True)
    company_address = serializers.CharField(source='company.address', read_only=True, allow_null=True)
    department_manager_name = serializers.CharField(source='department.manager.name', read_only=True, allow_null=True)
    employee_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'name', 'phone', 'avatar', 'position', 
            'department', 'department_name', 'company', 'company_name', 'company_address',
            'department_manager_name', 'employee_id', 'bio', 'date_joined', 'last_login'
        ]
        read_only_fields = [
            'id', 'email', 'date_joined', 'last_login', 'department_name', 
            'company_name', 'company_address', 'department_manager_name', 'employee_id'
        ]
    
    def get_employee_id(self, obj):
        if obj.company:
            # Count users in the same company who joined before this user
            return f"EMP{User.objects.filter(company=obj.company, date_joined__lt=obj.date_joined).count() + 1:04d}"
        return None


class CompanySerializer(serializers.ModelSerializer):
    """Serializer for Company model."""
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'short_name', 'industry', 'size', 'address', 'website', 'phone']


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model."""
    
    company_name = serializers.SerializerMethodField()
    manager_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'company', 'company_name', 'manager', 'manager_name', 'description', 'created_at']
    
    def get_company_name(self, obj):
        return obj.company.name if obj.company else None

    def get_manager_name(self, obj):
        if obj.manager:
            return obj.manager.name or obj.manager.username
        return None


class ContactSerializer(serializers.ModelSerializer):
    """联系人序列化器"""
    
    department_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    bio = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    class Meta:
        model = Contact
        fields = [
            'id', 'name', 'position', 'department', 'department_name', 'company', 
            'company_name', 'mobile', 'phone', 'email', 'office', 'employee_id', 
            'join_date', 'birthday', 'manager', 'skills', 'projects', 'user', 
            'created_at', 'updated_at', 'bio'
        ]
    
    def get_department_name(self, obj):
        return obj.department.name if obj.department else None
    
    def get_company_name(self, obj):
        return obj.company.name if obj.company else None


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new user."""
    
    confirmPassword = serializers.CharField(write_only=True, required=True)
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), 
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'name', 'password', 'confirmPassword', 'company', 'bio']
        extra_kwargs = {
            'password': {'write_only': True},
            'name': {'required': False},
            'bio': {'required': False}
        }
    
    def validate(self, attrs):
        """Validate that the passwords match."""
        if attrs['password'] != attrs.pop('confirmPassword'):
            raise serializers.ValidationError({"confirmPassword": _("密码不匹配")})
        return attrs
    
    def create(self, validated_data):
        """Create and return a new user."""
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            name=validated_data.get('name', ''),
            company=validated_data.get('company'),
            bio=validated_data.get('bio', '')
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for the user authentication object."""
    
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})
    remember = serializers.BooleanField(default=False)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset."""
    
    email = serializers.EmailField(required=True)


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for resetting a password."""
    
    token = serializers.CharField(required=True)
    newPassword = serializers.CharField(required=True, style={'input_type': 'password'})
    confirmPassword = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        """Validate that the passwords match."""
        if attrs['newPassword'] != attrs['confirmPassword']:
            raise serializers.ValidationError({"newPassword": "Password fields didn't match."})
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change endpoint."""
    
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        """Validate that the passwords match."""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs 