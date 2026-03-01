"""URL Configuration for the users app."""

from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from django.views.decorators.csrf import csrf_exempt

from .views import (
    RegisterView, 
    LoginView, 
    AdminLoginView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetView,
    UserViewSet,
    CompanyViewSet,
    DepartmentViewSet,
    ContactViewSet
)

# 创建路由器并注册viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'companies', CompanyViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'contacts', ContactViewSet)

# URL patterns
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('admin/login/', AdminLoginView.as_view(), name='admin_login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', PasswordResetView.as_view(), name='password_reset_confirm'),
    path('', include(router.urls)),
] 