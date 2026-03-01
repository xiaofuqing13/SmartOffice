"""Models for the AI app."""

from django.db import models
from django.contrib.auth import get_user_model
import os
import uuid

User = get_user_model()


class AIChat(models.Model):
    """Model to store AI chat history."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_chats')
    title = models.CharField(max_length=255, default='New Chat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"


class AIChatMessage(models.Model):
    """Model to store AI chat messages."""
    
    class MessageRole(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'
        SYSTEM = 'system', 'System'
    
    chat = models.ForeignKey(AIChat, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=MessageRole.choices)
    content = models.TextField()
    source = models.CharField(max_length=50, null=True, blank=True, help_text="消息来源，如'knowledge_base', 'general_ai'等")
    metadata = models.JSONField(null=True, blank=True, help_text="存储与消息相关的元数据，如文档ID")
    is_deleted = models.BooleanField(default=False, help_text="标记消息是否被删除")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class AIRecommendation(models.Model):
    """Model to store AI recommendations for users."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_recommendations')
    content = models.TextField()
    type = models.CharField(max_length=50)  # Type of recommendation (task, document, etc.)
    reference_id = models.IntegerField(null=True, blank=True)  # ID of the referenced object
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Recommendation for {self.user.username}: {self.content[:50]}..."


def document_upload_path(instance, filename):
    """为上传的文档生成路径，确保文档唯一性"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('documents', str(instance.user.id), filename)


class Document(models.Model):
    """存储用户上传的文档"""
    
    class DocumentStatus(models.TextChoices):
        PENDING = 'pending', '待处理'
        PROCESSING = 'processing', '处理中'
        COMPLETED = 'completed', '处理完成'
        FAILED = 'failed', '处理失败'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_documents')
    file = models.FileField(upload_to=document_upload_path)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    chat = models.ForeignKey(AIChat, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.PENDING)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.original_filename} - {self.user.username}"
        

class DocumentChunk(models.Model):
    """存储文档解析后的分块内容"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField()
    chunk_index = models.IntegerField()
    embedding = models.JSONField(null=True, blank=True)  # 存储文本向量化的结果
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['document', 'chunk_index']
        
    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.original_filename}" 