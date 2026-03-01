from rest_framework import serializers
from .models import UIPreference, AISetting


class UIPreferenceSerializer(serializers.ModelSerializer):
    """界面偏好设置序列化器"""
    
    class Meta:
        model = UIPreference
        fields = ['theme', 'content_density', 'font_size']
        read_only_fields = ['user']


class AISettingSerializer(serializers.ModelSerializer):
    """个性化AI设置序列化器"""
    
    class Meta:
        model = AISetting
        fields = ['nickname', 'job', 'tone', 'traits_text', 'other_info']
        read_only_fields = ['user'] 