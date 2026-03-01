from django.contrib import admin
from .models import Contract, ContractVersion, ContractAttachment, ContractAction, ContractTemplate

@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'contract_type', 'industry', 'scene', 'is_active', 'created_by', 'created_at')
    list_filter = ('contract_type', 'industry', 'scene', 'is_active')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'title', 'type', 'company', 'amount', 'created_by', 'created_at')
    list_filter = ('type', 'company')
    search_fields = ('title', 'number', 'company')
    date_hierarchy = 'created_at'

@admin.register(ContractVersion)
class ContractVersionAdmin(admin.ModelAdmin):
    list_display = ('id', 'contract', 'version', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('contract__title', 'contract__number')

@admin.register(ContractAttachment)
class ContractAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'contract', 'file_type', 'size', 'uploaded_by', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('name', 'contract__title')

@admin.register(ContractAction)
class ContractActionAdmin(admin.ModelAdmin):
    list_display = ('id', 'contract', 'user', 'action_type', 'created_at')
    list_filter = ('action_type', 'created_at')
    search_fields = ('contract__title', 'user__username', 'description') 