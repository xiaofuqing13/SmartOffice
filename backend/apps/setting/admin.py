from django.contrib import admin
from .models import UIPreference, AISetting


@admin.register(UIPreference)
class UIPreferenceAdmin(admin.ModelAdmin):
    """界面偏好设置后台管理"""
    list_display = ['user', 'theme', 'content_density', 'font_size', 'updated_at']
    list_filter = ['theme', 'content_density']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'updated_at'

@admin.register(AISetting)
class AISettingAdmin(admin.ModelAdmin):
    list_display = ('user', 'nickname', 'job', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'nickname', 'job')
    date_hierarchy = 'updated_at' 