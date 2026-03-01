from django.urls import path
from .views import UIPreferenceAPIView, AISettingAPIView

app_name = 'setting'

urlpatterns = [
    path('ui-preferences', UIPreferenceAPIView.as_view(), name='ui_preferences'),
    path('ai-settings', AISettingAPIView.as_view(), name='ai_settings'),
] 