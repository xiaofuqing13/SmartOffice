from rest_framework import serializers
from .models import CalendarEvent
from apps.users.serializers import UserSimpleSerializer

class CalendarEventSerializer(serializers.ModelSerializer):
    """日历事件序列化器"""
    creator_name = serializers.SerializerMethodField()
    participants_info = UserSimpleSerializer(source='participants', many=True, read_only=True)
    
    class Meta:
        model = CalendarEvent
        fields = [
            'id', 'title', 'start', 'end', 'location', 'description', 
            'type', 'reminder', 'creator', 'creator_name',
            'participants', 'participants_info', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_creator_name(self, obj):
        return obj.creator.username if obj.creator else None

class CalendarEventCreateSerializer(serializers.ModelSerializer):
    """创建日历事件序列化器"""
    
    class Meta:
        model = CalendarEvent
        fields = [
            'title', 'start', 'end', 'location', 'description', 
            'type', 'reminder', 'participants'
        ]
    
    def create(self, validated_data):
        participants = validated_data.pop('participants', [])
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['creator'] = request.user
        
        instance = super().create(validated_data)
        
        if participants:
            instance.participants.set(participants)
        
        # 默认将创建者添加为参与者
        if instance.creator not in instance.participants.all():
            instance.participants.add(instance.creator)
        
        return instance 