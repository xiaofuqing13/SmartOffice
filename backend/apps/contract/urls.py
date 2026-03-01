from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('contracts', views.ContractViewSet, basename='contract')
router.register('templates', views.ContractTemplateViewSet, basename='contract-template')

urlpatterns = [
    # 优先匹配手动添加的路由
    path('types/', views.ContractTypeListView.as_view(), name='contract-types'),
    path('industries/', views.IndustryListView.as_view(), name='contract-industries'),
    path('scenes/', views.SceneListView.as_view(), name='contract-scenes'),
    
    # 然后匹配router生成的路由
    path('', include(router.urls)),
    path('regulation-query/', views.RegulationQueryView.as_view(), name='regulation-query'),
] 