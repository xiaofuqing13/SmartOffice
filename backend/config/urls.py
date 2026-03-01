"""URL Configuration for smart-office project."""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.decorators.csrf import csrf_exempt
from apps.users.views import RegisterView, LoginView, LogoutView, PasswordResetRequestView, PasswordResetView

# API文档配置
schema_view = get_schema_view(
    openapi.Info(
        title="智能办公系统 API",
        default_version='v1',
        description="智能办公系统API文档",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# URL patterns
urlpatterns = [
    # 管理后台
    path('admin/', admin.site.urls),
    
    # 直接注册关键路由（绕过应用内URL）
    path('api/auth/register/', csrf_exempt(RegisterView.as_view())),
    path('api/auth/login/', csrf_exempt(LoginView.as_view())),
    path('api/auth/logout/', csrf_exempt(LogoutView.as_view())),
    path('api/auth/password/request-reset/', csrf_exempt(PasswordResetRequestView.as_view())),
    path('api/auth/password/reset/', csrf_exempt(PasswordResetView.as_view())),
    
    # API文档
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API路由
    path('api/auth/', include('apps.users.urls')),
    path('api/admin/', include('apps.admin.urls')),
    path('api/calendar/', include('apps.calendar.urls')),
    path('api/chat/', include('apps.chat.urls')),
    path('api/knowledge/', include('apps.knowledge.urls')),
    path('api/ai/', include('apps.ai.urls')),
    path('api/contract/', include('apps.contract.urls')),
    path('api/settings/', include('apps.setting.urls')),
    path('api/smartdoc/', include('apps.smartdoc.urls')),
    path('api/search/', include('apps.search.urls')),
    path('api/', include('apps.project.urls')),
]

# 开发环境下添加静态文件和媒体文件URL
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 