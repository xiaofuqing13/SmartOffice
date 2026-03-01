"""URL Configuration for the calendar app."""

from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import CalendarEventViewSet

# 创建路由器
router = DefaultRouter()
router.register(r'events', CalendarEventViewSet, basename='calendar-event')

# URL patterns
urlpatterns = router.urls 