from django.contrib import admin
from .models import Document, DocumentCategory, RelatedDocument

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'doc_type', 'creator', 'is_shared', 'created_at', 'updated_at')
    list_filter = ('doc_type', 'is_shared', 'created_at', 'updated_at')
    search_fields = ('title', 'content', 'doc_type')
    raw_id_fields = ('creator', 'last_edited_by', 'shared_with')
    date_hierarchy = 'updated_at'

@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'document_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')

@admin.register(RelatedDocument)
class RelatedDocumentAdmin(admin.ModelAdmin):
    list_display = ('source_document', 'related_document', 'relation_type', 'relevance_score', 'created_at')
    list_filter = ('relation_type', 'created_at')
    search_fields = ('source_document__title', 'related_document__title', 'relation_type')
    raw_id_fields = ('source_document', 'related_document')
