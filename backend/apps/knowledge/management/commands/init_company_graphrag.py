import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.users.models import Company
from apps.knowledge.models import CompanyKnowledgeBase

class Command(BaseCommand):
    help = '为每个公司初始化GraphRAG目录结构'

    def handle(self, *args, **options):
        # GraphRAG基础目录
        graphrag_dir = os.path.join(settings.BASE_DIR, 'graphrag-main')
        
        # 创建基本目录结构
        base_dirs = [
            os.path.join(graphrag_dir, 'ragtest', 'input'),
            os.path.join(graphrag_dir, 'ragtest', 'output'),
            os.path.join(graphrag_dir, 'ragtest', 'index'),
        ]
        
        for base_dir in base_dirs:
            if not os.path.exists(base_dir):
                os.makedirs(base_dir)
                self.stdout.write(self.style.SUCCESS(f'创建目录: {base_dir}'))
        
        # 获取所有公司
        companies = Company.objects.all()
        self.stdout.write(f'找到 {companies.count()} 个公司')
        
        # 为每个公司创建目录结构
        for company in companies:
            company_id = company.id
            company_name = company.name
            
            # 创建公司特定的目录
            company_dirs = [
                os.path.join(graphrag_dir, 'ragtest', 'input', f'company_{company_id}'),
                os.path.join(graphrag_dir, 'ragtest', 'output', f'company_{company_id}'),
                os.path.join(graphrag_dir, 'ragtest', 'index', f'company_{company_id}'),
            ]
            
            for company_dir in company_dirs:
                if not os.path.exists(company_dir):
                    os.makedirs(company_dir)
                    self.stdout.write(self.style.SUCCESS(f'为公司 {company_name} (ID: {company_id}) 创建目录: {company_dir}'))
            
            # 创建或更新公司知识库记录
            company_kb, created = CompanyKnowledgeBase.objects.get_or_create(
                company=company,
                defaults={
                    'status': 'pending',
                    'processing_message': '知识库尚未构建',
                    'index_path': os.path.join(graphrag_dir, 'ragtest', 'index', f'company_{company_id}'),
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'为公司 {company_name} 创建知识库记录'))
            else:
                self.stdout.write(f'公司 {company_name} 的知识库记录已存在')
        
        self.stdout.write(self.style.SUCCESS('所有公司的GraphRAG目录结构初始化完成')) 