from django.db import models
from django.contrib.auth import get_user_model
from apps.users.models import Company  # 统一只用users的Company

User = get_user_model()

class Project(models.Model):
    name = models.CharField(max_length=100)
    desc = models.TextField(blank=True, null=True)
    start = models.DateField(blank=True, null=True)
    end = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('doing','进行中'),('done','已完成')], default='doing')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects')
    members = models.ManyToManyField(User, related_name='projects', blank=True)
    def __str__(self):
        return self.name

class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=50, blank=True, null=True)
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='member_roles', null=True, blank=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'user', 'task'],
                name='unique_project_user_task'
            ),
            models.UniqueConstraint(
                fields=['project', 'user'],
                condition=models.Q(task__isnull=True),
                name='unique_project_user_global'
            )
        ]
    def __str__(self):
        return f"{self.user.username} - {self.project.name} - {self.task.title if self.task else '全局'}"

class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    assignee = models.ForeignKey(ProjectMember, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    due_date = models.DateField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=[('low','低'),('medium','中'),('high','高')], default='medium')
    status = models.CharField(max_length=20, choices=[('todo','待处理'),('in-progress','进行中'),('done','已完成')], default='todo')
    tags = models.CharField(max_length=100, blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tasks', verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    def __str__(self):
        return self.title

class ProjectDocument(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents', verbose_name='所属项目')
    name = models.CharField(max_length=255, verbose_name='文档名称')
    file = models.FileField(upload_to='project_documents/', verbose_name='文档文件')
    desc = models.TextField(blank=True, null=True, verbose_name='文档描述')
    tags = models.CharField(max_length=255, blank=True, null=True, verbose_name='标签')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    analysis = models.TextField(blank=True, null=True, verbose_name='AI分析')
    uploader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_documents', verbose_name='上传者')

    def __str__(self):
        return self.name

class TaskCompletion(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='completions')
    member = models.ForeignKey(ProjectMember, on_delete=models.CASCADE, related_name='task_completions')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('task', 'member')

    def __str__(self):
        return f"{self.member.user.username} - {self.task.title} - {'完成' if self.completed else '未完成'}"

class Requirement(models.Model):
    """项目需求模型"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='requirements', verbose_name='所属项目')
    name = models.CharField(max_length=100, verbose_name='需求名称')
    description = models.TextField(blank=True, null=True, verbose_name='需求描述')
    priority = models.CharField(max_length=10, choices=[('low','低'),('medium','中'),('high','高')], 
                              default='medium', verbose_name='优先级')
    status = models.CharField(max_length=20, 
                            choices=[('pending','待处理'),('in-progress','进行中'),('completed','已完成')],
                            default='pending', verbose_name='状态')
    tags = models.CharField(max_length=255, blank=True, null=True, verbose_name='标签')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='created_requirements', verbose_name='创建者')
    ai_analysis = models.TextField(blank=True, null=True, verbose_name='AI分析')
    
    def __str__(self):
        return self.name 