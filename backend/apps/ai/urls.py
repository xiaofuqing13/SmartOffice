"""URL Configuration for the AI app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AIChatViewSet,
    AIChatMessageViewSet,
    AIRecommendationViewSet,
    ChatAPIView,
    ContentGenerationAPIView,
    ScheduleReminderAPIView,
    DocumentViewSet,
    DocumentSearchAPIView,
    ChatWithDocumentsAPIView
)

# 创建路由器并注册viewsets
router = DefaultRouter()
router.register(r'chats', AIChatViewSet, basename='ai-chat')
router.register(r'messages', AIChatMessageViewSet, basename='ai-message')
router.register(r'recommendations', AIRecommendationViewSet, basename='ai-recommendation')
router.register(r'documents', DocumentViewSet, basename='ai-document')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path('chat/', ChatAPIView.as_view(), name='ai-chat-api'),
    path('generate/', ContentGenerationAPIView.as_view(), name='ai-generate'),
    path('schedule-reminder/', ScheduleReminderAPIView.as_view(), name='ai-schedule-reminder'),
    path('documents/search/', DocumentSearchAPIView.as_view(), name='ai-document-search'),
    path('chat-with-documents/', ChatWithDocumentsAPIView.as_view(), name='ai-chat-with-documents'),
] 