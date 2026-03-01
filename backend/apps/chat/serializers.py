"""Serializers for the chat app."""

from rest_framework import serializers
from .models import ChatSession, ChatParticipant, ChatMessage, ChatMessageRead
from apps.users.serializers import UserSerializer
from apps.knowledge.serializers import KnowledgeBaseSerializer
import logging


class ChatParticipantSerializer(serializers.ModelSerializer):
    """Serializer for chat participants."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatParticipant
        fields = ['id', 'user', 'is_admin', 'joined_at', 'last_read']
        read_only_fields = ['id', 'joined_at']


class ChatMessageReadSerializer(serializers.ModelSerializer):
    """Serializer for message read receipts."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatMessageRead
        fields = ['id', 'user', 'read_at']
        read_only_fields = ['id', 'read_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages."""
    
    sender = UserSerializer(read_only=True)
    read_receipts = ChatMessageReadSerializer(many=True, read_only=True)
    knowledge_detail = KnowledgeBaseSerializer(source='knowledge', read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'chat', 'sender', 'content', 'message_type', 
            'file', 'file_name', 'file_size', 'knowledge', 
            'knowledge_detail', 'calendar_data', 'created_at', 'read_receipts'
        ]
        read_only_fields = ['id', 'sender', 'file_size', 'created_at', 'read_receipts', 'calendar_data']


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat messages."""
    
    knowledge_id = serializers.IntegerField(required=False, write_only=True)
    
    class Meta:
        model = ChatMessage
        fields = [
            'chat', 'content', 'message_type', 'file', 'knowledge_id'
        ]
    
    def validate(self, attrs):
        """Validate the message data."""
        message_type = attrs.get('message_type')
        file = attrs.get('file')
        knowledge_id = attrs.pop('knowledge_id', None)
        
        # Check if file is provided for file/image message types
        if message_type in ['file', 'image'] and not file:
            raise serializers.ValidationError({"file": "文件类型的消息必须上传文件"})
            
        # Check if knowledge_id is provided for knowledge message type
        if message_type == 'knowledge' and not knowledge_id:
            raise serializers.ValidationError({"knowledge_id": "知识库类型的消息必须提供知识库ID"})
            
        # Add knowledge to validated data if provided
        if knowledge_id:
            from apps.knowledge.models import KnowledgeBase
            try:
                knowledge = KnowledgeBase.objects.get(id=knowledge_id)
                attrs['knowledge'] = knowledge
            except KnowledgeBase.DoesNotExist:
                raise serializers.ValidationError({"knowledge_id": "指定的知识库不存在"})
        
        return attrs


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for chat sessions."""
    
    participants = ChatParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'is_group', 'created_at', 'updated_at', 'participants', 'last_message', 'unread_count']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_last_message(self, obj):
        """Get the last message in the chat."""
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return {
                'id': last_message.id,
                'content': last_message.content,
                'sender': last_message.sender.username,
                'message_type': last_message.message_type,
                'created_at': last_message.created_at
            }
        return None
    
    def get_unread_count(self, obj):
        """Get the number of unread messages for the current user."""
        user = self.context.get('request').user
        try:
            participant = obj.participants.get(user=user)
            return obj.messages.filter(created_at__gt=participant.last_read).count()
        except ChatParticipant.DoesNotExist:
            return 0


class ChatSessionDetailSerializer(ChatSessionSerializer):
    """Detailed serializer for chat sessions."""
    
    messages = ChatMessageSerializer(many=True, read_only=True)
    
    class Meta(ChatSessionSerializer.Meta):
        fields = ChatSessionSerializer.Meta.fields + ['messages']


class ChatSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat sessions."""
    
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True
    )
    
    class Meta:
        model = ChatSession
        fields = ['title', 'is_group', 'participant_ids']
    
    def validate_participant_ids(self, value):
        """Validate participant IDs."""
        from apps.users.models import User
        
        logger = logging.getLogger(__name__)
        logger.info(f"validating participant_ids: {value}")
        
        # Check if all users exist
        existing_users = list(User.objects.filter(id__in=value).values_list('id', flat=True))
        logger.info(f"existing users: {existing_users}")
        
        if len(existing_users) != len(value):
            non_existing = set(value) - set(existing_users)
            logger.error(f"Non-existing user IDs: {non_existing}")
            raise serializers.ValidationError(f"用户ID {non_existing} 不存在")
        
        # Ensure current user is not in the list (will be added separately)
        current_user = self.context['request'].user
        logger.info(f"current user: {current_user.id}")
        
        # 记录是否包含当前用户
        has_current_user = current_user.id in value
        logger.info(f"包含当前用户: {has_current_user}")
        
        if has_current_user:
            value.remove(current_user.id)
            logger.info(f"已移除当前用户，剩余参与者: {value}")
            
        # For non-group chats, ensure there's exactly one participant
        is_group = self.initial_data.get('is_group', False)
        logger.info(f"is_group: {is_group}, participant count: {len(value)}")
        
        if not is_group:
            if len(value) == 0:
                if has_current_user:
                    logger.error("尝试创建与自己的聊天")
                    raise serializers.ValidationError("无法创建与自己的聊天，请选择其他联系人")
                else:
                    logger.error("没有指定参与者")
                    raise serializers.ValidationError("单聊必须指定一个参与者")
            elif len(value) > 1:
                logger.error(f"参与者过多: {len(value)}")
                raise serializers.ValidationError("单聊只能有一个参与者")
            
        return value
    
    def create(self, validated_data):
        """Create a new chat session with participants."""
        participant_ids = validated_data.pop('participant_ids')
        current_user = self.context['request'].user
        
        # Create the chat session
        chat_session = ChatSession.objects.create(**validated_data)
        
        # Add current user as admin
        ChatParticipant.objects.create(
            chat=chat_session,
            user=current_user,
            is_admin=True
        )
        
        # Add other participants
        from apps.users.models import User
        for user_id in participant_ids:
            user = User.objects.get(id=user_id)
            ChatParticipant.objects.create(
                chat=chat_session,
                user=user
            )
            
        return chat_session 