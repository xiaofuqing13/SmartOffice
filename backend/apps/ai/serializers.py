"""Serializers for the AI app."""

from rest_framework import serializers
from .models import AIChat, AIChatMessage, AIRecommendation, Document, DocumentChunk
import markdown
from .services import DocumentProcessor


class AIChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for AIChatMessage model."""
    content = serializers.SerializerMethodField()
    
    class Meta:
        model = AIChatMessage
        fields = ['id', 'role', 'content', 'created_at', 'source']
        read_only_fields = ['id', 'created_at']

    def get_content(self, obj):
        """Convert markdown content to HTML for assistant messages."""
        if obj.role == AIChatMessage.MessageRole.ASSISTANT:
            # Convert markdown to HTML, supporting extensions for tables and fenced code blocks
            return markdown.markdown(obj.content, extensions=['fenced_code', 'tables'])
        return obj.content


class AIChatListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for AI Chat lists."""
    title = serializers.SerializerMethodField()

    class Meta:
        model = AIChat
        fields = ['id', 'title', 'created_at', 'updated_at']

    def get_title(self, obj):
        """
        Return the chat title. If the title is empty, use the content
        of the first message as the title.
        """
        if obj.title:
            return obj.title
        
        first_message = obj.messages.order_by('created_at').first()
        if first_message:
            return first_message.content[:50]  # Use first 50 chars of the message
        
        return f"对话 {obj.id}"


class AIChatSerializer(serializers.ModelSerializer):
    """Serializer for AIChat model."""
    
    messages = AIChatMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = AIChat
        fields = ['id', 'user', 'title', 'messages', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class AIChatCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new AI chat."""
    
    class Meta:
        model = AIChat
        fields = ['title']


class AIMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new AI message."""
    
    class Meta:
        model = AIChatMessage
        fields = ['chat', 'role', 'content']
        read_only_fields = ['created_at']


class AIRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for AIRecommendation model."""
    
    class Meta:
        model = AIRecommendation
        fields = ['id', 'user', 'content', 'type', 'reference_id', 'is_read', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for chat requests."""
    
    message = serializers.CharField(required=True)
    chat_id = serializers.IntegerField(required=False, allow_null=True)


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat responses."""
    
    message = serializers.CharField()
    chat_id = serializers.IntegerField()


class ContentGenerationRequestSerializer(serializers.Serializer):
    """Serializer for content generation requests."""
    
    prompt = serializers.CharField(required=True)
    context = serializers.CharField(required=False, allow_blank=True)
    content_type = serializers.ChoiceField(
        choices=['text', 'email', 'meeting_summary', 'document'],
        default='text'
    )


class ContentGenerationResponseSerializer(serializers.Serializer):
    """Serializer for content generation responses."""
    
    content = serializers.CharField() 


class DocumentUploadSerializer(serializers.ModelSerializer):
    """上传文档的序列化器"""
    
    file = serializers.FileField(write_only=True, required=True)
    chat_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Document
        fields = ['id', 'file', 'chat_id', 'original_filename', 'file_type', 'status', 'created_at']
        read_only_fields = ['id', 'original_filename', 'file_type', 'status', 'created_at']

    def create(self, validated_data):
        file_obj = validated_data.pop('file')
        user = self.context['request'].user
        
        # 使用DocumentProcessor来获取文件类型
        processor = DocumentProcessor()
        if not processor.is_supported_file(file_obj):
            raise serializers.ValidationError({'error': '不支持的文件类型'})
        
        file_type = processor.get_file_type(file_obj)
        
        document = Document.objects.create(
            user=user,
            file=file_obj,
            original_filename=file_obj.name,
            file_type=file_type,
            status=Document.DocumentStatus.PENDING,
            **validated_data
        )
        return document


class DocumentSerializer(serializers.ModelSerializer):
    """文档模型的序列化器"""
    
    class Meta:
        model = Document
        fields = ['id', 'user', 'file', 'original_filename', 'file_type', 'chat', 'status', 'error_message', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class DocumentChunkSerializer(serializers.ModelSerializer):
    """文档块的序列化器"""
    
    class Meta:
        model = DocumentChunk
        fields = ['id', 'document', 'content', 'chunk_index', 'created_at']
        read_only_fields = ['id', 'document', 'created_at']


class DocumentSearchRequestSerializer(serializers.Serializer):
    """文档搜索请求序列化器"""
    
    query = serializers.CharField(required=True)
    limit = serializers.IntegerField(required=False, default=5)
    document_id = serializers.IntegerField(required=False)  # 可选，指定要搜索的文档


class DocumentSearchResponseSerializer(serializers.Serializer):
    """文档搜索响应序列化器"""
    
    results = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )


class ChatWithDocumentsRequestSerializer(serializers.Serializer):
    """文档增强聊天请求序列化器."""
    
    message = serializers.CharField(required=False, allow_blank=True)
    chat_id = serializers.IntegerField(required=False, allow_null=True)
    document_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        default=list
    )
    chatMode = serializers.CharField(required=False, default='agent')
    method = serializers.CharField(required=False, default='local')
    ai_settings = serializers.DictField(required=False, allow_null=True) 