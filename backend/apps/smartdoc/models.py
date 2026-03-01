from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class DocumentCategory(models.Model):
    """文档分类模型"""
    name = models.CharField(max_length=100, verbose_name="分类名称")
    color = models.CharField(max_length=20, default="#409EFF", verbose_name="分类颜色")
    description = models.TextField(blank=True, null=True, verbose_name="分类描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="document_categories", verbose_name="所属用户", null=True)

    class Meta:
        verbose_name = "文档分类"
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.name
    
    @property
    def document_count(self):
        return self.documents.count()

class Document(models.Model):
    """智能文档模型"""
    title = models.CharField(max_length=255, verbose_name="文档标题")
    content = models.TextField(blank=True, default="", verbose_name="文档内容")
    doc_type = models.CharField(max_length=50, default="通用", verbose_name="文档类型")
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents", verbose_name="所属分类")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_documents", verbose_name="创建者")
    is_shared = models.BooleanField(default=False, verbose_name="是否共享")
    shared_with = models.ManyToManyField(User, related_name="shared_documents", blank=True, verbose_name="共享用户")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    last_edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="last_edited_documents", verbose_name="最后编辑者")
    
    class Meta:
        verbose_name = "智能文档"
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.title
        
    def get_preview(self):
        """获取文档预览内容"""
        preview_length = 100
        if len(self.content) <= preview_length:
            return self.content
        return self.content[:preview_length] + "..."

class DocumentSharePermission(models.Model):
    """文档共享权限模型"""
    PERMISSION_CHOICES = (
        ('read', '只读'),
        ('edit', '编辑'),
    )
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="permissions", verbose_name="文档")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="document_permissions", verbose_name="用户")
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='read', verbose_name="权限")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        verbose_name = "文档共享权限"
        verbose_name_plural = verbose_name
        unique_together = ('document', 'user')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.document.title} - {self.user.username} - {self.get_permission_display()}"

class RelatedDocument(models.Model):
    """相关文档模型（用于上下文感知）"""
    source_document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="related_documents", verbose_name="源文档")
    related_document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="related_to", verbose_name="相关文档")
    relation_type = models.CharField(max_length=50, default="相关", verbose_name="关联类型")
    relevance_score = models.FloatField(default=0.0, verbose_name="相关度分数")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        verbose_name = "相关文档"
        verbose_name_plural = verbose_name
        unique_together = ('source_document', 'related_document')
        ordering = ['-relevance_score']
    
    def __str__(self):
        return f"{self.source_document.title} -> {self.related_document.title}"
