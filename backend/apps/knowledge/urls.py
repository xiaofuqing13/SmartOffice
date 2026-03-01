"""URL Configuration for the knowledge app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    KnowledgeCategoryViewSet, 
    KnowledgeBaseViewSet, 
    KnowledgeChunkViewSet, 
    KnowledgeBaseBuildView,
    GraphRAGQueryView,
    KnowledgeGraphDataView,
    KnowledgeEntityDetailView
)

# 创建路由器
router = DefaultRouter()
router.register(r'categories', KnowledgeCategoryViewSet)
router.register(r'documents', KnowledgeBaseViewSet)
router.register(r'chunks', KnowledgeChunkViewSet)

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path('build/', KnowledgeBaseBuildView.as_view(), name='build-knowledge-base'),
    path('build/status/', KnowledgeBaseBuildView.as_view(), name='knowledge-base-status'),
    path('query/', GraphRAGQueryView.as_view(), name='knowledge-query'),
    path('graph-data/', KnowledgeGraphDataView.as_view(), name='knowledge-graph-data'),
    path('entities/<str:entity_id>/', KnowledgeEntityDetailView.as_view(), name='knowledge-entity-detail'),
]