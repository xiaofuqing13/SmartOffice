"""
管理命令，用于将没有公司关联的用户分配到默认公司
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.users.models import User, Company


class Command(BaseCommand):
    help = '将没有公司关联的用户分配到默认公司'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company_id',
            type=int,
            help='指定默认公司ID，如果不指定则使用第一个公司'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始将用户关联到公司...'))
        
        # 获取默认公司
        company_id = options.get('company_id')
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
                self.stdout.write(f'使用指定公司: {company.name} (ID: {company.id})')
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'指定的公司ID {company_id} 不存在!'))
                return
        else:
            # 获取第一个公司作为默认公司
            try:
                company = Company.objects.first()
                if not company:
                    self.stdout.write(self.style.ERROR('没有找到任何公司! 请先创建至少一个公司。'))
                    return
                self.stdout.write(f'使用默认公司: {company.name} (ID: {company.id})')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'获取默认公司失败: {str(e)}'))
                return
        
        # 获取没有公司关联的用户
        users_without_company = User.objects.filter(company__isnull=True)
        count = users_without_company.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('所有用户已经关联了公司，无需操作。'))
            return
        
        self.stdout.write(f'找到 {count} 个没有公司关联的用户')
        
        # 确认操作
        confirmation = input(f'确定要将这 {count} 个用户关联到 {company.name} 吗? (y/n): ')
        if confirmation.lower() != 'y':
            self.stdout.write(self.style.WARNING('操作已取消。'))
            return
        
        # 更新用户的公司关联
        with transaction.atomic():
            updated = users_without_company.update(company=company)
            
        self.stdout.write(self.style.SUCCESS(f'成功将 {updated} 个用户关联到公司 {company.name}。'))
        
        # 提示运行同步联系人命令
        self.stdout.write(self.style.WARNING('请记得运行 python manage.py sync_contacts 命令来更新联系人记录。')) 