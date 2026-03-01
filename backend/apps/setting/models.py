from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class UIPreference(models.Model):
    """用户界面偏好设置模型"""
    
    THEME_CHOICES = (
        ('light', '浅色'),
        ('dark', '深色'),
    )
    
    CONTENT_DENSITY_CHOICES = (
        ('compact', '紧凑'),
        ('normal', '标准'),
        ('comfortable', '宽松'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ui_preference', verbose_name='用户')
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light', verbose_name='主题模式')
    content_density = models.CharField(max_length=15, choices=CONTENT_DENSITY_CHOICES, default='normal', verbose_name='内容密度')
    font_size = models.IntegerField(default=14, verbose_name='字体大小')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '界面偏好'
        verbose_name_plural = verbose_name
        
    def __str__(self):
        return f"{self.user.username}的界面设置"


class AISetting(models.Model):
    """用户个性化AI设置模型"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ai_setting', verbose_name='用户')
    nickname = models.CharField(max_length=50, blank=True, null=True, verbose_name='AI称呼用户')
    job = models.CharField(max_length=100, blank=True, null=True, verbose_name='用户职业')
    tone = models.CharField(max_length=20, default='professional', verbose_name='沟通风格')
    traits_text = models.TextField(blank=True, null=True, verbose_name='AI特征')
    other_info = models.TextField(blank=True, null=True, verbose_name='其他信息')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = 'AI个性化设置'
        verbose_name_plural = verbose_name
        
    def __str__(self):
        return f"{self.user.username}的AI设置" 