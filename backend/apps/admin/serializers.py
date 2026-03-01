from rest_framework import serializers
from apps.users.models import User, Company, Department
from apps.smartdoc.models import Document
from apps.contract.models import Contract, ContractTemplate
from apps.knowledge.models import KnowledgeBase, KnowledgeCategory

class UserAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model for admin purposes.
    Includes all necessary fields for user management.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    is_department_manager = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'name', 'phone', 
            'position', 'is_staff', 'is_active', 'last_login', 
            'date_joined', 'company', 'department', 'company_name', 'department_name',
            'is_department_manager'
        ]
        read_only_fields = ['last_login', 'date_joined']

    def get_is_department_manager(self, obj):
        return obj.managed_departments.exists()

class CompanyAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for the Company model for admin purposes.
    """
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'short_name', 'industry', 'size', 'address', 
            'website', 'phone', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class DepartmentAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for the Department model for admin purposes.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    manager_name = serializers.SerializerMethodField()
    manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        required=False, 
        allow_null=True
    )
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'company', 'company_name', 'manager', 'manager_name', 'description']

    def get_manager_name(self, obj):
        if obj.manager:
            return obj.manager.name or obj.manager.username
        return None

class SmartDocAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for the Document model for admin smartdoc view.
    """
    company_name = serializers.CharField(source='creator.company.name', read_only=True, default='N/A')
    creator_name = serializers.CharField(source='creator.name', read_only=True, default='N/A')

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'content', 'doc_type', 'company_name', 'creator_name', 
            'is_shared', 'created_at', 'updated_at'
        ]

class ContractTemplateAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for the ContractTemplate model in the admin panel.
    """
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ContractTemplate
        fields = [
            'id', 'name', 'description', 'contract_type', 'industry', 
            'scene', 'content', 'is_active', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_created_by_name(self, obj):
        if obj.created_by:
            # 优先使用name字段，如果为空则使用username
            return obj.created_by.name or obj.created_by.username
        return None

class ContractAdminListSerializer(serializers.ModelSerializer):
    """
    Serializer for the Contract model for admin list view (without content).
    """
    company_name = serializers.CharField(source='created_by.company.name', read_only=True, default='N/A')
    creator_name = serializers.CharField(source='created_by.name', read_only=True, default='N/A')
    created_by_name = serializers.ReadOnlyField(source='created_by.name')

    class Meta:
        model = Contract
        fields = [
            'id', 'title', 'number', 'type', 'amount', 
            'company_name', 'creator_name', 'created_by_name', 'created_at'
        ]

class ContractAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for the Contract model for admin detail view.
    """
    company_name = serializers.CharField(source='created_by.company.name', read_only=True, default='N/A')
    creator_name = serializers.CharField(source='created_by.name', read_only=True, default='N/A')

    class Meta:
        model = Contract
        fields = [
            'id', 'title', 'number', 'type', 'amount', 'company', 'content',
            'company_name', 'creator_name', 
            'sign_date', 'start_date', 'expire_date', 'created_at'
        ]

class KnowledgeCategoryAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for the KnowledgeCategory model for admin purposes.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = KnowledgeCategory
        fields = ['id', 'name', 'description', 'company', 'company_name', 'icon', 'color']
    
    def validate_company(self, value):
        # Ensure the selected company belongs to the owner
        if not value:
            raise serializers.ValidationError("必须为分类选择一个公司。")
        
        request = self.context.get('request')
        if request and hasattr(request.user, 'owned_companies'):
            if not request.user.owned_companies.filter(id=value.id).exists():
                raise serializers.ValidationError("您无权将分类分配给该公司。")
        return value

class KnowledgeBaseAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for the KnowledgeBase model for admin purposes.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    creator_name = serializers.SerializerMethodField()
    # 允许上传文件，但在更新时不是必须的
    original_file = serializers.FileField(write_only=True, required=False, allow_null=True)
    category = serializers.PrimaryKeyRelatedField(queryset=KnowledgeCategory.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = KnowledgeBase
        fields = [
            'id', 'title', 'description', 'company', 'company_name', 
            'category', 'category_name', 'creator', 'creator_name', 'created_at', 'updated_at',
            'original_file', 'original_filename', 'file_type', 'file_size'
        ]
        read_only_fields = ['creator', 'created_at', 'updated_at', 'original_filename', 'file_type', 'file_size']

    def get_creator_name(self, obj):
        if obj.creator:
            return obj.creator.name or obj.creator.username
        return '未知'

    def create(self, validated_data):
        if 'original_file' not in validated_data:
            raise serializers.ValidationError({'original_file': '必须上传一个文件。'})
        # 文件本身由视图处理，这里只创建元数据
        validated_data.pop('original_file', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # 文件由视图处理，这里只更新元数据
        validated_data.pop('original_file', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        # 不在此处保存，由视图逻辑完成最终保存
        return instance

    def validate_company(self, value):
        # Ensure the selected company belongs to the owner
        if not value:
            raise serializers.ValidationError("必须为知识库选择一个公司。")
        
        request = self.context.get('request')
        if request and hasattr(request.user, 'owned_companies'):
            if not request.user.owned_companies.filter(id=value.id).exists():
                raise serializers.ValidationError("您无权将知识库分配给该公司。")
        return value
        
    def validate_category(self, value):
        # Ensure the selected category belongs to the owner's companies, if provided
        request = self.context.get('request')
        if value and request and hasattr(request.user, 'owned_companies') and not KnowledgeCategory.objects.filter(
            id=value.id, 
            company__in=request.user.owned_companies.all()
        ).exists():
            raise serializers.ValidationError("所选分类无效或不属于您的公司。")
        return value 