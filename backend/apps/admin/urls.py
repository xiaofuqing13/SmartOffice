from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardDataView, 
    AdminUserViewSet, 
    AdminCompanyViewSet, 
    AdminDepartmentViewSet,
    SmartDocAdminViewSet,
    ContractAdminViewSet,
    KnowledgeBaseAdminViewSet,
    KnowledgeCategoryAdminViewSet,
    AdminKnowledgeBuildView,
    DashboardAnalysisView,
    AdminContractTemplateViewSet
)

router = DefaultRouter()
router.register(r'users', AdminUserViewSet, basename='admin-users')
router.register(r'companies', AdminCompanyViewSet, basename='admin-companies')
router.register(r'departments', AdminDepartmentViewSet, basename='admin-departments')
router.register(r'smart-docs', SmartDocAdminViewSet, basename='admin-smart-docs')
router.register(r'contracts', ContractAdminViewSet, basename='admin-contracts')
router.register(r'contract-templates', AdminContractTemplateViewSet, basename='admin-contract-templates')
router.register(r'knowledge-categories', KnowledgeCategoryAdminViewSet, basename='admin-knowledge-categories')
router.register(r'knowledge-bases', KnowledgeBaseAdminViewSet, basename='admin-knowledge-bases')

urlpatterns = [
    path('dashboard/', DashboardDataView.as_view(), name='admin-dashboard'),
    path('dashboard/analysis/', DashboardAnalysisView.as_view(), name='admin-dashboard-analysis'),
    path('knowledge/build/', AdminKnowledgeBuildView.as_view(), name='admin-knowledge-build'),
    path('', include(router.urls)),
] 