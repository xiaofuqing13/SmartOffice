from rest_framework import serializers
from .models import Contract, ContractVersion, ContractAttachment, ContractAction, ContractTemplate
from django.contrib.auth import get_user_model

User = get_user_model()

class UserBriefSerializer(serializers.ModelSerializer):
    """用户简要信息序列化器"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class ContractAttachmentSerializer(serializers.ModelSerializer):
    """合同附件序列化器"""
    uploaded_by = UserBriefSerializer(read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ContractAttachment
        fields = ['id', 'name', 'file', 'file_type', 'size', 'uploaded_by', 'uploaded_by_name', 'uploaded_at']
        read_only_fields = ['id', 'file_type', 'size', 'uploaded_by', 'uploaded_at']
    
    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.username if obj.uploaded_by else None

class ContractActionSerializer(serializers.ModelSerializer):
    """合同操作记录序列化器"""
    user = UserBriefSerializer(read_only=True)
    
    class Meta:
        model = ContractAction
        fields = ['id', 'user', 'action_type', 'description', 'created_at']
        read_only_fields = ['created_at']

class ContractListSerializer(serializers.ModelSerializer):
    """合同列表序列化器"""
    
    class Meta:
        model = Contract
        fields = ['id', 'number', 'title', 'type', 'company', 'amount', 
                  'created_at', 'expire_date']

class ContractDetailSerializer(serializers.ModelSerializer):
    """合同详情序列化器"""
    attachments = ContractAttachmentSerializer(many=True, read_only=True)
    created_by_name = serializers.SerializerMethodField()
    template_info = serializers.SerializerMethodField()
    actions = ContractActionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Contract
        fields = ['id', 'number', 'title', 'type', 'company', 'amount',
                  'sign_date', 'start_date', 'expire_date',
                  'content', 'remark', 'created_by', 
                  'created_by_name', 'created_at', 'updated_at', 
                  'attachments', 'template', 'template_info',
                  'actions']
        read_only_fields = ['id', 'number', 'created_by', 'created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        return obj.created_by.username if obj.created_by else None

    def get_template_info(self, obj):
        if obj.template:
            return {
                'id': obj.template.id,
                'name': obj.template.name,
                'contract_type': obj.template.contract_type,
                'industry': obj.template.industry,
                'scene': obj.template.scene,
                'description': obj.template.description,
                'is_active': obj.template.is_active,
                'created_at': obj.template.created_at,
                'updated_at': obj.template.updated_at
            }
        return None

class ContractCreateSerializer(serializers.ModelSerializer):
    """合同创建序列化器"""
    use_ai_agent = serializers.BooleanField(required=False, default=False, write_only=True)
    description = serializers.CharField(required=False, write_only=True)
    template_id = serializers.IntegerField(required=False, write_only=True)
    # 添加筛选字段，设为write_only确保不传给模型
    industry = serializers.CharField(required=False, write_only=True)
    scene = serializers.CharField(required=False, write_only=True)
    
    class Meta:
        model = Contract
        fields = ['title', 'type', 'company', 'amount', 'sign_date', 
                  'start_date', 'expire_date', 'content', 'remark', 
                  'template', 'use_ai_agent', 
                  'description', 'template_id', 'industry', 'scene']
    
    def validate(self, data):
        # 验证AI生成必须提供描述
        use_ai_agent = data.get('use_ai_agent', False)
        description = data.get('description', '')
        
        if use_ai_agent and not description:
            raise serializers.ValidationError({'description': '使用AI生成时必须提供合同描述'})
            
        # 验证模板ID并设置模板
        template_id = data.pop('template_id', None)
        if template_id:
            try:
                template = ContractTemplate.objects.get(id=template_id, is_active=True)
                data['template'] = template
                # 如果没有提供内容，使用模板内容
                if not data.get('content'):
                    data['content'] = template.content
            except ContractTemplate.DoesNotExist:
                raise serializers.ValidationError({'template_id': '指定的模板不存在或未启用'})
        
        return data
        
    def create(self, validated_data):
        """重写创建方法，移除非模型字段"""
        # 移除不属于模型的字段
        use_ai_agent = validated_data.pop('use_ai_agent', False)
        description = validated_data.pop('description', None)
        # 移除筛选字段
        validated_data.pop('industry', None)
        validated_data.pop('scene', None)
        
        # 创建合同实例
        return Contract.objects.create(**validated_data)

class ContractUpdateSerializer(serializers.ModelSerializer):
    """合同更新序列化器"""
    
    class Meta:
        model = Contract
        fields = ['title', 'type', 'company', 'amount', 'sign_date', 
                 'start_date', 'expire_date', 'content', 'remark', 
                 'template']

class ContractTemplateListSerializer(serializers.ModelSerializer):
    """合同模板列表序列化器"""
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ContractTemplate
        fields = ['id', 'name', 'contract_type', 'industry', 'scene', 'description', 
                  'is_active', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']
    
    def get_created_by_name(self, obj):
        return obj.created_by.username if obj.created_by else None

class ContractTemplateDetailSerializer(serializers.ModelSerializer):
    """合同模板详情序列化器"""
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ContractTemplate
        fields = ['id', 'name', 'contract_type', 'industry', 'scene', 'description', 
                  'content', 'is_active', 'created_by', 'created_by_name', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        return obj.created_by.username if obj.created_by else None

class ContractTemplateCreateUpdateSerializer(serializers.ModelSerializer):
    """合同模板创建和更新序列化器"""
    class Meta:
        model = ContractTemplate
        fields = ['name', 'contract_type', 'industry', 'scene', 
                  'description', 'content', 'is_active'] 