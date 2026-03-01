"""Models for the chat app."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.users.models import User
from apps.knowledge.models import KnowledgeBase
import uuid
import os


def chat_file_path(instance, filename):
    """Generate file path for a chat file."""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('chat_files', filename)


class ChatSession(models.Model):
    """Model representing a chat session between users."""
    
    title = models.CharField(_('Title'), max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    is_group = models.BooleanField(_('Is Group Chat'), default=False)
    
    class Meta:
        verbose_name = _('Chat Session')
        verbose_name_plural = _('Chat Sessions')
        ordering = ['-updated_at']
        
    def __str__(self):
        return self.title or f"Chat {self.id}"


class ChatParticipant(models.Model):
    """Model representing a participant in a chat session."""
    
    chat = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    is_admin = models.BooleanField(_('Is Admin'), default=False)
    joined_at = models.DateTimeField(_('Joined At'), auto_now_add=True)
    last_read = models.DateTimeField(_('Last Read'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Chat Participant')
        verbose_name_plural = _('Chat Participants')
        unique_together = ('chat', 'user')
        
    def __str__(self):
        return f"{self.user.username} in {self.chat}"


class ChatMessage(models.Model):
    """Model representing a message in a chat session."""
    
    class MessageType(models.TextChoices):
        TEXT = 'text', _('Text')
        FILE = 'file', _('File')
        IMAGE = 'image', _('Image')
        KNOWLEDGE = 'knowledge', _('Knowledge')
        CALENDAR = 'calendar', _('Calendar')
    
    chat = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(_('Content'))
    message_type = models.CharField(_('Message Type'), max_length=10, choices=MessageType.choices, default=MessageType.TEXT)
    file = models.FileField(_('File'), upload_to=chat_file_path, blank=True, null=True)
    file_name = models.CharField(_('File Name'), max_length=255, blank=True, null=True)
    file_size = models.PositiveIntegerField(_('File Size (KB)'), default=0)
    knowledge = models.ForeignKey(KnowledgeBase, on_delete=models.SET_NULL, related_name='shared_in_chats', blank=True, null=True)
    calendar_data = models.JSONField(_('Calendar Data'), blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Chat Message')
        verbose_name_plural = _('Chat Messages')
        ordering = ['created_at']
        
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"
    
    def save(self, *args, **kwargs):
        # Calculate file size if file exists
        if self.file and hasattr(self.file, 'size'):
            self.file_size = self.file.size // 1024  # Convert to KB
            if not self.file_name:
                self.file_name = os.path.basename(self.file.name)
                
        super().save(*args, **kwargs)


class ChatMessageRead(models.Model):
    """Model representing read status of a message."""
    
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='read_receipts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_messages')
    read_at = models.DateTimeField(_('Read At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Message Read Receipt')
        verbose_name_plural = _('Message Read Receipts')
        unique_together = ('message', 'user')
        
    def __str__(self):
        return f"{self.user.username} read {self.message} at {self.read_at}" 