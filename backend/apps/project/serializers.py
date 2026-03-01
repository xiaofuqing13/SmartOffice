from rest_framework import serializers
from .models import Company, Project, ProjectMember, Task, ProjectDocument, TaskCompletion, Requirement
from django.contrib.auth import get_user_model
import logging

User = get_user_model()

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'email']

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='user', write_only=True)
    class Meta:
        model = ProjectMember
        fields = ['id', 'user', 'user_id', 'role']

class ProjectSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    company_id = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), source='company', write_only=True)
    class Meta:
        model = Project
        fields = ['id', 'name', 'desc', 'start', 'end', 'status', 'company_id', 'members']

    def create(self, validated_data):
        members = validated_data.pop('members', [])
        project = super().create(validated_data)
        project.members.set(members)
        return project

    def update(self, instance, validated_data):
        members = validated_data.pop('members', None)
        project = super().update(instance, validated_data)
        if members is not None:
            project.members.set(members)
        return project

class TaskSerializer(serializers.ModelSerializer):
    assignee = ProjectMemberSerializer(read_only=True)
    assignee_id = serializers.CharField(write_only=True, allow_null=True, required=False)
    assignee_name = serializers.SerializerMethodField()
    creator_name = serializers.SerializerMethodField()
    class Meta:
        model = Task
        fields = ['id', 'project', 'title', 'description', 'assignee', 'assignee_id', 
                  'due_date', 'priority', 'status', 'tags',
                  'assignee_name', 'creator_name', 'created_at', 'updated_at']

    def get_creator_name(self, obj):
        if obj.creator:
            return obj.creator.name or obj.creator.username
        return "未知用户"

    def get_assignee_name(self, obj):
        if obj.assignee and obj.assignee.user:
            return obj.assignee.user.name or obj.assignee.user.username
        return "未分配"
        
    def validate_assignee_id(self, value):
        """支持直接传入User的id作为assignee_id，如果不存在对应的ProjectMember则自动创建"""
        if value is None:
            return None
        if isinstance(value, str) and value.isdigit() or isinstance(value, int):
            try:
                user_id = int(value)
                project_id = self.initial_data.get('project')
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    raise serializers.ValidationError(f"用户ID {user_id} 不存在")
                if project_id:
                    project_member = ProjectMember.objects.filter(
                        user_id=user_id, 
                        project_id=project_id
                    ).first()
                    if project_member:
                        return project_member.id  # 只返回id
                    try:
                        project = Project.objects.get(id=project_id)
                        project_member = ProjectMember.objects.create(
                            user=user,
                            project=project,
                            role="成员"
                        )
                        return project_member.id  # 只返回id
                    except Project.DoesNotExist:
                        raise serializers.ValidationError(f"项目ID {project_id} 不存在")
                else:
                    project_member = ProjectMember.objects.filter(user_id=user_id).first()
                    if project_member:
                        return project_member.id
                    raise serializers.ValidationError("缺少项目ID，无法创建项目成员")
            except ValueError:
                raise serializers.ValidationError("无效的用户ID格式")
        # 如果是ProjectMember对象或ID，直接返回id
        try:
            if isinstance(value, str) and not value.isdigit():
                project_member = ProjectMember.objects.get(id=value)
                return project_member.id
            if isinstance(value, ProjectMember):
                return value.id
            return value
        except (ProjectMember.DoesNotExist, ValueError):
            raise serializers.ValidationError(f"项目成员ID {value} 不存在")

class ProjectDocumentSerializer(serializers.ModelSerializer):
    uploader = UserSimpleSerializer(read_only=True)
    uploader_name = serializers.SerializerMethodField()
    class Meta:
        model = ProjectDocument
        fields = ['id', 'project', 'name', 'file', 'desc', 'tags', 'uploaded_at', 'analysis', 'uploader', 'uploader_name']

    def get_uploader_name(self, obj):
        if obj.uploader:
            return obj.uploader.name or obj.uploader.username
        return "未知用户"

class TaskCompletionSerializer(serializers.ModelSerializer):
    member = ProjectMemberSerializer(read_only=True)
    member_id = serializers.PrimaryKeyRelatedField(queryset=ProjectMember.objects.all(), source='member', write_only=True)
    user = serializers.SerializerMethodField()
    class Meta:
        model = TaskCompletion
        fields = ['id', 'task', 'member', 'member_id', 'completed', 'completed_at', 'user']
    def get_user(self, obj):
        try:
            if obj.member and obj.member.user:
                return {
                    'id': obj.member.user.id,
                    'username': obj.member.user.username,
                    'email': obj.member.user.email
                }
        except Exception:
            return None
        return None

class RequirementSerializer(serializers.ModelSerializer):
    """需求序列化器"""
    creator = UserSimpleSerializer(read_only=True)
    creator_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='creator', write_only=True, required=False)
    tags_list = serializers.SerializerMethodField()
    creator_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Requirement
        fields = ['id', 'project', 'name', 'description', 'priority', 'status', 
                 'tags', 'tags_list', 'created_at', 'updated_at', 'creator', 'creator_id', 'ai_analysis',
                 'creator_name']
    
    def get_creator_name(self, obj):
        if obj.creator:
            return obj.creator.name or obj.creator.username
        return "未知用户"
    
    def get_tags_list(self, obj):
        """将逗号分隔的标签转为列表"""
        if not obj.tags:
            return []
        tags = obj.tags.split(',')
        return [{'text': tag.strip(), 'type': 'primary'} for tag in tags if tag.strip()]
    
    def create(self, validated_data):
        """创建需求时处理标签格式"""
        # 获取request中的用户作为creator
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['creator'] = request.user
        return super().create(validated_data) 