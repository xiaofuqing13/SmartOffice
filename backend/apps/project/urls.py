from rest_framework import routers
from .views import ProjectViewSet, ProjectMemberViewSet, TaskViewSet, CompanyViewSet, ProjectDocumentViewSet, TaskCompletionViewSet, RequirementViewSet

router = routers.DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'project-members', ProjectMemberViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'companies', CompanyViewSet)
router.register(r'project-documents', ProjectDocumentViewSet, basename='project-document')
router.register(r'task-completions', TaskCompletionViewSet, basename='task-completion')
router.register(r'requirements', RequirementViewSet, basename='requirement')

urlpatterns = router.urls 