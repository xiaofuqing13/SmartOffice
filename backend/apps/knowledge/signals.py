"""Signal handlers for the knowledge app."""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import KnowledgeBase

logger = logging.getLogger(__name__)


@receiver(post_save, sender=KnowledgeBase)
def process_knowledge_file(sender, instance, created, **kwargs):
    """Process the file when a knowledge base document is created."""
    if created and instance.file and instance.status == 'pending':
        logger.info(f"新文件上传至知识库: {instance.title}")
        # 在实际应用中，这里会启动异步任务进行文件处理
        # 例如： tasks.process_knowledge_file.delay(instance.id) 

@receiver(post_delete, sender=KnowledgeBase)
def delete_knowledgebase_files(sender, instance, **kwargs):
    """
    当 KnowledgeBase 对象被删除时，从文件系统中删除对应的文件。
    """
    try:
        if instance.file:
            instance.file.delete(save=False)
            logger.info(f"已删除转换后的文件: {instance.file.name}")
    except Exception as e:
        logger.error(f"删除转换后的文件失败 {instance.file.name}: {e}")

    try:
        if instance.original_file:
            instance.original_file.delete(save=False)
            logger.info(f"已删除原始文件: {instance.original_file.name}")
    except Exception as e:
        logger.error(f"删除原始文件失败 {instance.original_file.name}: {e}") 