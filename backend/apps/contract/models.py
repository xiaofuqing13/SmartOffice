from django.db import models
from django.conf import settings
import uuid
import os

def contract_file_path(instance, filename):
    """为合同文件生成存储路径"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('contracts', str(instance.contract.id), filename)

class ContractTemplate(models.Model):
    """合同模板模型"""
    name = models.CharField(max_length=200, verbose_name='模板名称')
    description = models.TextField(blank=True, verbose_name='模板描述')
    contract_type = models.CharField(max_length=50, verbose_name='合同类型')
    industry = models.CharField(max_length=50, blank=True, verbose_name='行业领域')
    scene = models.CharField(max_length=50, blank=True, verbose_name='交易场景')
    content = models.TextField(verbose_name='模板内容')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_templates',
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '合同模板'
        verbose_name_plural = '合同模板列表'
        ordering = ['contract_type', 'name']
    
    def __str__(self):
        return self.name

class Contract(models.Model):
    """合同模型"""
    # 基本信息
    number = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name='合同编号')
    title = models.CharField(max_length=200, verbose_name='合同标题')
    type = models.CharField(max_length=50, verbose_name='合同类型')
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='合同金额')
    company = models.CharField(max_length=200, verbose_name='签约对方')
    
    # 日期信息
    sign_date = models.DateField(null=True, blank=True, verbose_name='签约日期')
    start_date = models.DateField(null=True, blank=True, verbose_name='生效日期')
    expire_date = models.DateField(null=True, blank=True, verbose_name='到期日期')
    
    # 内容信息
    content = models.TextField(blank=True, verbose_name='合同内容')
    remark = models.TextField(blank=True, verbose_name='备注')
    
    # 关联信息
    template = models.ForeignKey(
        ContractTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracts',
        verbose_name='使用的模板'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_contracts',
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '合同'
        verbose_name_plural = '合同列表'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.number} - {self.title}"

    def save(self, *args, **kwargs):
        # 新创建的合同自动生成编号
        if not self.number:
            # 根据当前年月和顺序号生成编号
            from django.utils import timezone
            today = timezone.now()
            prefix = f"CT-{today.year}{today.month:02d}"
            
            # 查找最后一个使用此前缀的合同
            last_contract = Contract.objects.filter(
                number__startswith=prefix
            ).order_by('number').last()
            
            if last_contract:
                # 提取编号后的序号并加1
                try:
                    last_id = int(last_contract.number.split('-')[-1])
                    self.number = f"{prefix}-{last_id + 1:04d}"
                except:
                    self.number = f"{prefix}-0001"
            else:
                # 没有找到同前缀的合同，从1开始
                self.number = f"{prefix}-0001"
        
        super().save(*args, **kwargs)

class ContractVersion(models.Model):
    """合同版本历史"""
    contract = models.ForeignKey(
        Contract, 
        on_delete=models.CASCADE, 
        related_name='versions',
        verbose_name='关联合同'
    )
    version = models.PositiveIntegerField(verbose_name='版本号')
    content = models.TextField(verbose_name='合同内容')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '合同版本'
        verbose_name_plural = '合同版本列表'
        unique_together = ('contract', 'version')
        ordering = ['-version']
    
    def __str__(self):
        return f"{self.contract.number} - 版本 {self.version}"

class ContractAttachment(models.Model):
    """合同附件"""
    contract = models.ForeignKey(
        Contract, 
        on_delete=models.CASCADE, 
        related_name='attachments',
        verbose_name='关联合同'
    )
    name = models.CharField(max_length=200, verbose_name='附件名称')
    file = models.FileField(upload_to=contract_file_path, verbose_name='附件文件')
    file_type = models.CharField(max_length=20, blank=True, verbose_name='文件类型')
    size = models.PositiveIntegerField(default=0, verbose_name='文件大小(KB)')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name='上传人'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    
    class Meta:
        verbose_name = '合同附件'
        verbose_name_plural = '合同附件列表'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # 自动识别文件类型和大小
        if self.file:
            filename = self.file.name.lower()
            if filename.endswith('.pdf'):
                self.file_type = 'pdf'
            elif filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                self.file_type = 'image'
            else:
                self.file_type = 'other'
                
            # 计算文件大小（KB）
            if hasattr(self.file, 'size'):
                self.size = self.file.size // 1024
                
        super().save(*args, **kwargs)

class ContractAction(models.Model):
    """合同操作记录"""
    contract = models.ForeignKey(
        Contract, 
        on_delete=models.CASCADE, 
        related_name='actions',
        verbose_name='关联合同'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name='操作人'
    )
    action_type = models.CharField(max_length=50, verbose_name='操作类型')
    description = models.TextField(verbose_name='操作描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')
    
    class Meta:
        verbose_name = '合同操作记录'
        verbose_name_plural = '合同操作记录列表'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} {self.action_type} {self.contract.number}" 