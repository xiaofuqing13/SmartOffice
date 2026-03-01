"""User models for the smart-office project."""

from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom user manager for User model with email as the unique identifier."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class Company(models.Model):
    """Company model for storing company information."""
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_companies', verbose_name=_('company owner'), null=True, blank=True)
    name = models.CharField(_('company name'), max_length=255)
    short_name = models.CharField(_('short name'), max_length=100, blank=True, null=True)
    industry = models.CharField(_('industry'), max_length=100, blank=True, null=True)
    size = models.CharField(_('company size'), max_length=50, blank=True, null=True)
    address = models.CharField(_('address'), max_length=255, blank=True, null=True)
    website = models.CharField(_('website'), max_length=255, blank=True, null=True)
    phone = models.CharField(_('phone'), max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('company')
        verbose_name_plural = _('companies')
    
    def __str__(self):
        return self.name


class Department(models.Model):
    """Department model for storing department information."""
    
    name = models.CharField(_('department name'), max_length=100)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments', verbose_name='所属公司')
    manager = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments', verbose_name='部门经理')
    description = models.TextField(_('description'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('department')
        verbose_name_plural = _('departments')
    
    def __str__(self):
        return f"{self.company.name} - {self.name}"


class User(AbstractUser):
    """Custom User model with email as the unique identifier."""
    
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer.'),
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    name = models.CharField(_('full name'), max_length=150, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(_('phone number'), max_length=20, blank=True, null=True)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', blank=True, null=True)
    position = models.CharField(_('position'), max_length=100, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, related_name='users', blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, related_name='users', blank=True, null=True)
    bio = models.TextField(_('bio'), blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        # 如果提供了name但没有first_name和last_name，则拆分name
        if self.name and not (self.first_name or self.last_name):
            name_parts = self.name.split(' ', 1)
            if len(name_parts) > 1:
                self.first_name, self.last_name = name_parts
            else:
                self.first_name = name_parts[0]
                self.last_name = ''
        # 如果提供了first_name和last_name但没有name，则合并为name
        elif (self.first_name or self.last_name) and not self.name:
            self.name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)


class Contact(models.Model):
    """联系人模型，用于存储联系人信息"""
    
    name = models.CharField(_('姓名'), max_length=100)
    position = models.CharField(_('职位'), max_length=100, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, related_name='contacts', blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, related_name='contacts', blank=True, null=True)
    mobile = models.CharField(_('手机号码'), max_length=20, blank=True, null=True)
    phone = models.CharField(_('工作电话'), max_length=20, blank=True, null=True)
    email = models.EmailField(_('电子邮箱'), blank=True, null=True)
    office = models.CharField(_('办公地点'), max_length=255, blank=True, null=True)
    employee_id = models.CharField(_('员工编号'), max_length=50, blank=True, null=True)
    join_date = models.DateField(_('入职日期'), blank=True, null=True)
    birthday = models.DateField(_('出生日期'), blank=True, null=True)
    manager = models.CharField(_('直系领导'), max_length=100, blank=True, null=True)
    skills = models.JSONField(_('技能专长'), default=list, blank=True, null=True)
    projects = models.JSONField(_('管理项目'), default=list, blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='contact_profile', blank=True, null=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('联系人')
        verbose_name_plural = _('联系人')
        
    def __str__(self):
        return self.name


class PasswordResetToken(models.Model):
    """Model for password reset tokens."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(_('token'), max_length=255, unique=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'))
    used = models.BooleanField(_('used'), default=False)
    
    class Meta:
        verbose_name = _('password reset token')
        verbose_name_plural = _('password reset tokens')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reset token for {self.user.email}"
    
    @property
    def is_valid(self):
        """Check if the token is valid (not expired and not used)."""
        from django.utils import timezone
        return not self.used and self.expires_at > timezone.now() 