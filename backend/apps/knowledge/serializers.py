"""Serializers for the knowledge app."""

from rest_framework import serializers
from .models import KnowledgeCategory, KnowledgeBase, KnowledgeChunk
import os


class KnowledgeCategorySerializer(serializers.ModelSerializer):
    """Serializer for the KnowledgeCategory model."""
    document_count = serializers.SerializerMethodField()
    # creator = serializers.StringRelatedField(read_only=True) # Example if you want to show creator name

    class Meta:
        model = KnowledgeCategory
        fields = ['id', 'name', 'description', 'icon', 'color', 
                  'created_at', 'updated_at', 'document_count', 'creator'] # Added creator
        read_only_fields = ['creator'] # Assuming creator is set by perform_create or similar
    
    def get_document_count(self, obj):
        """Get the number of documents in this category."""
        try:
            return obj.knowledge_documents.count()
        except AttributeError:
            # 如果knowledge_documents关系不存在，返回0
            return 0


class KnowledgeChunkSerializer(serializers.ModelSerializer):
    """Serializer for the KnowledgeChunk model."""
    
    class Meta:
        model = KnowledgeChunk
        fields = ['id', 'chunk_index', 'content', 'metadata', 
                  'created_at', 'updated_at']


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    """Serializer for the KnowledgeBase model."""
    category_name = serializers.SerializerMethodField()
    creator_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    original_file_url = serializers.SerializerMethodField()
    tags_list = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()
    
    class Meta:
        model = KnowledgeBase
        fields = ['id', 'title', 'description', 'file', 'file_url', 'original_file', 'original_file_url', 'file_type', 
                  'file_size', 'category', 'category_name', 'tags', 'tags_list',
                  'status', 'processing_message', 'chunk_size', 'chunk_overlap',
                  'creator', 'creator_name', 'company', 'company_name', 'created_at', 'updated_at', 
                  'is_public', 'view_count', 'download_count']
        read_only_fields = ['file_size', 'file_type', 'status', 'processing_message',
                           'created_at', 'updated_at', 'view_count', 'download_count']
    
    def get_category_name(self, obj):
        """Get the category name."""
        if obj.category:
            return obj.category.name
        return None
    
    def get_creator_name(self, obj):
        """Get the creator's full name."""
        if obj.creator:
            return obj.creator.get_full_name() or obj.creator.username
        return None
    
    def get_file_url(self, obj):
        """Get the file URL."""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_original_file_url(self, obj):
        """Get the original file URL."""
        if obj.original_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.original_file.url)
            return obj.original_file.url
        return None
    
    def get_tags_list(self, obj):
        """Convert tags string to list."""
        if obj.tags:
            return [tag.strip() for tag in obj.tags.split(',')]
        return []
    
    def get_company_name(self, obj):
        """Get the company name."""
        if obj.company:
            return obj.company.name
        return None
        
    def get_file_type(self, obj):
        """Get the file type from metadata."""
        if obj.metadata and isinstance(obj.metadata, dict) and 'file_type' in obj.metadata:
            return obj.metadata['file_type']
        # 尝试从原始文件名获取
        elif obj.original_filename:
            ext = os.path.splitext(obj.original_filename)[1].lower().replace('.', '')
            return ext
        return None


class KnowledgeBaseDetailSerializer(KnowledgeBaseSerializer):
    """Detailed serializer for the KnowledgeBase model including chunks."""
    chunks = KnowledgeChunkSerializer(many=True, read_only=True)
    
    class Meta(KnowledgeBaseSerializer.Meta):
        fields = KnowledgeBaseSerializer.Meta.fields + ['chunks']


class KnowledgeBaseUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading knowledge base documents."""
    
    class Meta:
        model = KnowledgeBase
        fields = [
            'title', 'description', 'file', 'category', 'tags', 
            'chunk_size', 'chunk_overlap', 'is_public', 'company',
            'original_filename'
        ]
        read_only_fields = ['original_filename']


    def create(self, validated_data):
        """Create a knowledge base document."""
        request = self.context.get('request')
        
        uploaded_file = request.FILES.get('file') 
        
        if uploaded_file:
            validated_data['original_filename'] = uploaded_file.name
            
            if not validated_data.get('title'):
                base_name, _ = os.path.splitext(uploaded_file.name)
                validated_data['title'] = base_name

        validated_data['creator'] = request.user
        
        # 如果未提供公司，则使用用户所属公司
        if not validated_data.get('company') and request.user.company:
            validated_data['company'] = request.user.company
            
        validated_data['status'] = 'pending' 
        
        return super().create(validated_data) 