"""URL Configuration for the chat app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChatSessionViewSet, 
    ChatMessageViewSet,
    ChatMessageReadViewSet,
    FindOrCreateChatView,
    AnalyzeForCalendarView
)

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'sessions', ChatSessionViewSet, basename='chatsession')
router.register(r'messages', ChatMessageViewSet, basename='chatmessage')
router.register(r'reads', ChatMessageReadViewSet, basename='chatmessageread')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path('find-or-create/', FindOrCreateChatView.as_view(), name='find-or-create-chat'),
    path('analyze-for-calendar/', AnalyzeForCalendarView.as_view(), name='analyze-for-calendar'),
] 