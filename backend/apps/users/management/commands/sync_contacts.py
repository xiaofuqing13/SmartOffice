"""
管理命令，用于将用户数据同步到联系人表
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.users.models import User, Contact


class Command(BaseCommand):
    help = '将User表数据同步到Contact表，确保每个用户都有对应的联系人记录'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始同步用户数据到联系人表...'))
        
        # 获取所有用户
        all_users = User.objects.all()
        self.stdout.write(f'找到 {all_users.count()} 个用户')
        
        # 获取有公司关联的用户
        users_with_company = all_users.filter(company__isnull=False)
        self.stdout.write(f'其中 {users_with_company.count()} 个用户有公司关联')
        
        # 获取没有公司关联的用户
        users_without_company = all_users.filter(company__isnull=True)
        if users_without_company.exists():
            self.stdout.write(self.style.WARNING(f'警告: {users_without_company.count()} 个用户没有公司关联，建议先运行 python manage.py assign_company 命令'))
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        with transaction.atomic():
            for user in all_users:
                if user.company is None:
                    self.stdout.write(self.style.WARNING(f'跳过没有公司关联的用户: {user.username} (ID: {user.id})'))
                    skipped_count += 1
                    continue
                
                try:
                    # 如果用户没有关联的联系人，则创建
                    contact, created = Contact.objects.get_or_create(
                        user=user,
                        defaults={
                            'name': user.get_full_name() or user.username,
                            'position': user.position,
                            'department': user.department,
                            'company': user.company,
                            'mobile': user.phone,
                            'email': user.email,
                            'office': '',  # 可以根据需要设置默认值
                            'employee_id': '',  # 可以根据需要设置默认值
                            'skills': [],  # 设置空技能列表
                            'projects': []  # 设置空项目列表
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f'创建联系人: {user.username} -> {contact.name}')
                    else:
                        # 更新联系人信息
                        contact.name = user.get_full_name() or user.username
                        contact.position = user.position
                        contact.department = user.department
                        contact.company = user.company
                        contact.mobile = user.phone
                        contact.email = user.email
                        contact.save()
                        updated_count += 1
                        self.stdout.write(f'更新联系人: {user.username} -> {contact.name}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'处理用户 {user.username} 时出错: {str(e)}'))
                    error_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'同步完成! 新创建 {created_count} 个联系人，更新 {updated_count} 个联系人，跳过 {skipped_count} 个用户，出错 {error_count} 个。')) 