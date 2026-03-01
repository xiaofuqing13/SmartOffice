from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, DocumentCategoryViewSet, AIGenerateDocumentView

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'categories', DocumentCategoryViewSet, basename='document-category')

urlpatterns = [
    path('', include(router.urls)),
    path('ai_generate/', AIGenerateDocumentView.as_view(), name='ai-generate-document'),
] 