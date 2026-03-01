from rest_framework import serializers
from .models import Document, DocumentCategory, RelatedDocument, DocumentSharePermission
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSimpleSerializer(serializers.ModelSerializer):
    """用户简单序列化器"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class DocumentCategorySerializer(serializers.ModelSerializer):
    """文档分类序列化器"""
    document_count = serializers.SerializerMethodField()
    user = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = DocumentCategory
        fields = ['id', 'name', 'color', 'description', 'document_count', 'created_at', 'updated_at', 'user']
    
    def get_document_count(self, obj):
        """获取文档数量"""
        return obj.documents.count()

class DocumentSharePermissionSerializer(serializers.ModelSerializer):
    """文档共享权限序列化器"""
    user = UserSimpleSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    permission_display = serializers.CharField(source='get_permission_display', read_only=True)
    
    class Meta:
        model = DocumentSharePermission
        fields = ['id', 'user', 'user_id', 'permission', 'permission_display', 'created_at']
        
    def create(self, validated_data):
        return DocumentSharePermission.objects.create(**validated_data)

class DocumentListSerializer(serializers.ModelSerializer):
    """文档列表序列化器"""
    creator = UserSimpleSerializer(read_only=True)
    category = DocumentCategorySerializer(read_only=True)
    preview = serializers.SerializerMethodField()
    type = serializers.CharField(source='doc_type')
    update_time = serializers.DateTimeField(source='updated_at')
    create_time = serializers.DateTimeField(source='created_at')
    
    class Meta:
        model = Document
        fields = ['id', 'title', 'preview', 'type', 'category', 'creator', 
                  'is_shared', 'update_time', 'create_time']
    
    def get_preview(self, obj):
        return obj.get_preview()

class RelatedDocumentSerializer(serializers.ModelSerializer):
    """相关文档序列化器"""
    title = serializers.CharField(source='related_document.title', read_only=True)
    type = serializers.CharField(source='related_document.doc_type', read_only=True)
    source = serializers.CharField(source='relation_type', read_only=True)
    related_document_id = serializers.IntegerField(source='related_document.id', read_only=True)
    
    class Meta:
        model = RelatedDocument
        fields = ['id', 'title', 'type', 'source', 'relevance_score', 'related_document_id']

class DocumentDetailSerializer(serializers.ModelSerializer):
    """文档详情序列化器"""
    creator = UserSimpleSerializer(read_only=True)
    category = DocumentCategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    last_edited_by = UserSimpleSerializer(read_only=True)
    shared_with = UserSimpleSerializer(many=True, read_only=True)
    permissions = DocumentSharePermissionSerializer(many=True, read_only=True)
    related_documents = RelatedDocumentSerializer(many=True, read_only=True)
    type = serializers.CharField(source='doc_type')
    update_time = serializers.DateTimeField(source='updated_at', read_only=True)
    create_time = serializers.DateTimeField(source='created_at', read_only=True)
    
    class Meta:
        model = Document
        fields = ['id', 'title', 'content', 'type', 'category', 'creator', 
                  'is_shared', 'shared_with', 'permissions', 'update_time', 'create_time', 
                  'last_edited_by', 'related_documents', 'category_id']
    
    def create(self, validated_data):
        # 从validated_data中提取嵌套数据
        if 'doc_type' in validated_data:
            doc_type = validated_data.pop('doc_type')
        else:
            doc_type = '通用'
        
        # 不在这里设置creator和last_edited_by，这些字段由视图的perform_create方法设置
        document = Document.objects.create(
            **validated_data,
            doc_type=doc_type
        )
        return document
    
    def update(self, instance, validated_data):
        # 处理嵌套的doc_type数据
        if 'doc_type' in validated_data:
            instance.doc_type = validated_data.pop('doc_type')
        
        request = self.context.get('request')
        if request and request.user:
            instance.last_edited_by = request.user
        
        # 手动处理 category_id 更新
        category_id = validated_data.pop('category_id', None)
        if category_id is not None:
            try:
                category = DocumentCategory.objects.get(id=category_id)
                instance.category = category
            except DocumentCategory.DoesNotExist:
                # 如果找不到分类，可以选择忽略或抛出错误
                pass # 或者 raise serializers.ValidationError(...)
        elif 'category_id' in self.initial_data and category_id is None:
             # 处理解除分类关联的情况
            instance.category = None
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

    def to_internal_value(self, data):
        """将输入数据转换为内部表示形式前处理它们"""
        ret = super().to_internal_value(data)
        
        # 处理type字段到doc_type的映射
        if 'type' in data:
            ret['doc_type'] = data['type']
        
        return ret 