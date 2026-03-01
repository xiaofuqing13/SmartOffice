from django.contrib import admin
from .models import Company, Project, ProjectMember, Task
 
admin.site.register(Company)
admin.site.register(Project)
admin.site.register(ProjectMember)
admin.site.register(Task) 