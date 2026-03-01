"""Application configuration for knowledge app."""

from django.apps import AppConfig


class KnowledgeConfig(AppConfig):
    """Configuration for the knowledge app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.knowledge'
    verbose_name = '知识库管理'

    def ready(self):
        """Import signals when app is ready."""
        import apps.knowledge.signals 