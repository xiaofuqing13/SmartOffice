"""Models for the knowledge app."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.users.models import User, Company
import uuid
import os
from django.utils.text import slugify
from django.conf import settings
from .storage import GraphRAGStorage


def knowledge_file_path(instance, filename):
    """
    生成安全的文件名，不含路径
    文件将保存在GraphRAG存储的公司特定目录中
    确保只存储txt文件
    """
    # 从路径中只获取文件名部分
    actual_filename = os.path.basename(filename)
    base_name, ext = os.path.splitext(actual_filename)
    # 安全处理文件名
    safe_base_name = slugify(base_name)
    if not safe_base_name:
        safe_base_name = uuid.uuid4().hex[:8]
    
    # 生成文件名（使用.txt扩展名）
    file_name = f"{safe_base_name}.txt"
    
    # 如果实例有公司属性，则使用公司ID创建子目录
    if hasattr(instance, 'company') and instance.company:
        company_id = f"company_{instance.company.id}"
        # 返回公司特定的路径
        return os.path.join(company_id, file_name)
    
    # 如果没有公司，则放在无公司目录下
    return os.path.join('no_company', file_name)


def original_file_path(instance, filename):
    """
    为原始文件生成路径
    将文件保存在 media/original_files/company_X/ 目录下
    """
    # 从路径中只获取文件名部分
    actual_filename = os.path.basename(filename)
    base_name, ext = os.path.splitext(actual_filename)
    # 安全处理文件名
    safe_base_name = slugify(base_name)
    if not safe_base_name:
        safe_base_name = uuid.uuid4().hex[:8]
    
    # 生成文件名（保留原始扩展名）
    file_name = f"{safe_base_name}{ext}"
    
    # 使用当前日期创建子目录
    from datetime import datetime
    now = datetime.now()
    date_path = now.strftime("%Y/%m/%d")
    
    # 如果实例有公司属性，则使用公司ID创建子目录
    if hasattr(instance, 'company') and instance.company:
        company_id = f"company_{instance.company.id}"
        # 返回公司特定的路径
        return os.path.join('original_files', company_id, date_path, file_name)
    
    # 如果没有公司，则放在无公司目录下
    return os.path.join('original_files', 'no_company', date_path, file_name)


class KnowledgeCategory(models.Model):
    """Model representing a knowledge category."""
    name = models.CharField(_('Category Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True, null=True)
    icon = models.CharField(_('Icon'), max_length=50, default='Document')
    color = models.CharField(_('Color'), max_length=20, default='#007bff')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='knowledge_categories', null=True, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    creator = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        related_name='created_knowledge_categories', 
        null=True, 
        blank=True,
        verbose_name=_('Creator')
    )

    class Meta:
        verbose_name = _('Knowledge Category')
        verbose_name_plural = _('Knowledge Categories')
        ordering = ['name']

    def __str__(self):
        return self.name


class KnowledgeBase(models.Model):
    """Model representing a knowledge base document."""

    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    )

    FILE_TYPE_CHOICES = (
        ('pdf', _('PDF Document')),
        ('doc', _('Word Document')),
        ('xls', _('Excel Spreadsheet')),
        ('ppt', _('PowerPoint Presentation')),
        ('txt', _('Text File')),
        ('md', _('Markdown File')),
        ('img', _('Image')),
        ('other', _('Other')),
    )

    title = models.CharField(_('Title'), max_length=255)
    description = models.TextField(_('Description'), blank=True, null=True)
    # 使用自定义存储类和文件路径函数，保存到GraphRAG目录
    # 但在上传时不会自动保存，而是在process_file中手动处理后保存
    file = models.FileField(_('File'), upload_to=knowledge_file_path, storage=GraphRAGStorage(), blank=True, null=True)
    original_file = models.FileField(_('Original File'), upload_to=original_file_path, blank=True, null=True)
    original_filename = models.CharField(_('Original Filename'), max_length=512, blank=True, null=True)
    file_type = models.CharField(_('File Type'), max_length=10, choices=FILE_TYPE_CHOICES, default='other')
    file_size = models.PositiveIntegerField(_('File Size (KB)'), default=0)
    category = models.ForeignKey(KnowledgeCategory, on_delete=models.SET_NULL, 
                                related_name='knowledge_documents', null=True, blank=True) # Changed related_name
    tags = models.CharField(_('Tags'), max_length=255, blank=True, null=True, 
                         help_text=_('Comma-separated tags'))
    
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    processing_message = models.TextField(_('Processing Message'), blank=True, null=True)
    chunk_size = models.PositiveIntegerField(_('Chunk Size'), default=1000, 
                                          help_text=_('Size of text chunks for processing'))
    chunk_overlap = models.PositiveIntegerField(_('Chunk Overlap'), default=200,
                                             help_text=_('Overlap between chunks'))
    
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='knowledge_base_documents') # Changed related_name
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='knowledge_base_documents', null=True, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    is_public = models.BooleanField(_('Is Public'), default=False)
    view_count = models.PositiveIntegerField(_('View Count'), default=0)
    download_count = models.PositiveIntegerField(_('Download Count'), default=0)
    
    # 添加元数据字段，用于存储文件哈希和其他信息
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True, null=True)

    class Meta:
        verbose_name = _('Knowledge Base')
        verbose_name_plural = _('Knowledge Bases')
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
    def get_file_extension(self):
        filename_for_ext = self.original_filename if self.original_filename else (self.file.name if self.file else None)
        if filename_for_ext:
            return os.path.splitext(filename_for_ext)[1].lower().replace('.', '')
        return ''
    
    def save(self, *args, **kwargs):
        ext_to_check = self.get_file_extension()

        if ext_to_check:
            if ext_to_check in ['pdf']: self.file_type = 'pdf'
            elif ext_to_check in ['doc', 'docx']: self.file_type = 'doc'
            elif ext_to_check in ['xls', 'xlsx']: self.file_type = 'xls'
            elif ext_to_check in ['ppt', 'pptx']: self.file_type = 'ppt'
            elif ext_to_check == 'txt': self.file_type = 'txt'
            elif ext_to_check == 'md': self.file_type = 'md'
            elif ext_to_check in ['jpg', 'jpeg', 'png', 'gif', 'svg']: self.file_type = 'img'
            else: self.file_type = 'other'
        else:
            self.file_type = 'other'
            
        if self.file and hasattr(self.file, 'size'):
            self.file_size = self.file.size // 1024
            
        # 如果是新上传的文件并且没有设置原始文件名，则保存原始文件名
        if self.file and not self.original_filename and hasattr(self.file, 'name'):
            self.original_filename = os.path.basename(self.file.name)
            
        # 从文件名或文件URL中提取文件类型
        if not self.file_type and self.original_filename:
            self.file_type = os.path.splitext(self.original_filename)[1].lower().lstrip('.')
            
        super().save(*args, **kwargs)


class KnowledgeChunk(models.Model):
    """Model representing a chunk of text from a knowledge base document."""
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, 
                                     related_name='chunks')
    content = models.TextField(_('Content'))
    chunk_index = models.PositiveIntegerField(_('Chunk Index'))
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True)
    embedding = models.BinaryField(_('Vector Embedding'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Knowledge Chunk')
        verbose_name_plural = _('Knowledge Chunks')
        ordering = ['knowledge_base', 'chunk_index']
        unique_together = ['knowledge_base', 'chunk_index']

    def __str__(self):
        return f"{self.knowledge_base.title} - Chunk {self.chunk_index}" 


class CompanyKnowledgeBase(models.Model):
    """Model representing a company knowledge base."""

    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='knowledge_bases')
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    processing_message = models.TextField(_('Processing Message'), blank=True, null=True)
    total_documents = models.PositiveIntegerField(_('Total Documents'), default=0)
    total_chunks = models.PositiveIntegerField(_('Total Chunks'), default=0)
    index_path = models.CharField(_('Index Path'), max_length=512, blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    last_built_at = models.DateTimeField(_('Last Built At'), blank=True, null=True)
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='triggered_knowledge_bases', null=True, blank=True)
    
    # 保存构建配置和结果的元数据
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True, null=True)

    class Meta:
        verbose_name = _('Company Knowledge Base')
        verbose_name_plural = _('Company Knowledge Bases')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Knowledge Base for {self.company.name}" 