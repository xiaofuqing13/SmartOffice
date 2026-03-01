from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.users.models import User, Company, Department
from rest_framework import viewsets, filters, status
from django.db.models import Q, Count, F
from django.utils import timezone
from datetime import timedelta
import random
from rest_framework.pagination import PageNumberPagination
from django.db import transaction

from .serializers import (
    UserAdminSerializer, CompanyAdminSerializer, 
    DepartmentAdminSerializer, SmartDocAdminSerializer, ContractAdminSerializer,
    ContractAdminListSerializer, KnowledgeBaseAdminSerializer, KnowledgeCategoryAdminSerializer,
    ContractTemplateAdminSerializer
)
from apps.smartdoc.models import Document
from apps.contract.models import Contract, ContractTemplate
from apps.knowledge.models import KnowledgeBase, KnowledgeCategory, CompanyKnowledgeBase

import os
import logging
from django.conf import settings
from django.core.files.base import ContentFile
import pypdf  # 替代PyMuPDF
import docx  # python-docx
import textract
import tempfile
import threading
import subprocess
import yaml
from dotenv import load_dotenv
import traceback
import shutil

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

logger = logging.getLogger(__name__)

# 支持的文件类型及其处理方法
SUPPORTED_FILE_TYPES = {
    'pdf': 'extract_text_from_pdf',
    'doc': 'extract_text_from_doc',
    'docx': 'extract_text_from_doc',
    'txt': 'copy_text_file',
    'md': 'copy_text_file',
    'ppt': 'extract_text_from_ppt',
    'pptx': 'extract_text_from_ppt',
    'xls': 'extract_text_from_excel',
    'xlsx': 'extract_text_from_excel',
}

def extract_text_from_pdf(file_path):
    try:
        text = ""
        with open(file_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\\n\\n"
        return text
    except Exception as e:
        logger.error(f"PDF文本提取失败: {e}")
        return f"文件处理错误: {e}"

def extract_text_from_doc(file_path):
    try:
        if file_path.endswith('.docx'):
            doc = docx.Document(file_path)
            return "\\n\\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        else:
            return textract.process(file_path).decode('utf-8', errors='replace')
    except Exception as e:
        logger.error(f"Word文档文本提取失败: {e}")
        return f"文件处理错误: {e}"

def copy_text_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        logger.error(f"文本文件读取失败: {e}")
        return f"文件处理错误: {e}"

def extract_text_from_ppt(file_path):
    try:
        return textract.process(file_path).decode('utf-8', errors='replace')
    except Exception as e:
        logger.error(f"PPT文本提取失败: {e}")
        return f"文件处理错误: {e}"

def extract_text_from_excel(file_path):
    try:
        return textract.process(file_path).decode('utf-8', errors='replace')
    except Exception as e:
        logger.error(f"Excel文本提取失败: {e}")
        return f"文件处理错误: {e}"

def process_uploaded_file(instance, uploaded_file):
    temp_file_path = None
    try:
        # 使用 tempfile 创建一个安全的临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as temp_f:
            for chunk in uploaded_file.chunks():
                temp_f.write(chunk)
            temp_file_path = temp_f.name
        
        # 此时，with代码块结束，文件已由本程序关闭，可以安全地交给其他库处理
        file_ext = os.path.splitext(uploaded_file.name)[-1].lower().strip('.')
        handler_name = SUPPORTED_FILE_TYPES.get(file_ext)

        if not handler_name:
            instance.status = 'failed'
            instance.processing_message = f"不支持的文件类型: {file_ext}"
            instance.save()
            return

        handler = globals()[handler_name]
        text_content = handler(temp_file_path)
        
        # 将提取的文本内容保存到instance.file字段
        txt_filename = os.path.splitext(os.path.basename(uploaded_file.name))[0] + '.txt'
        instance.file.save(txt_filename, ContentFile(text_content.encode('utf-8')), save=False)
        
        instance.status = 'completed'
        instance.processing_message = '文件处理成功'

    except Exception as e:
        logger.error(f"处理上传文件时出错: {e}")
        instance.status = 'failed'
        instance.processing_message = str(e)
    finally:
        # 确保无论成功与否，都保存实例状态并清理临时文件
        instance.save()
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

class DashboardAnalysisView(APIView):
    """
    接收图表数据并返回AI分析结果
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            chart_title = request.data.get('chart_title')
            chart_data = request.data.get('chart_data')

            if not chart_title or not chart_data:
                return Response(
                    {"error": "必须提供图表标题和数据。"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 1. 加载AI配置
            config_path = os.path.join(settings.BASE_DIR, 'setting.yaml')
            if not os.path.exists(config_path):
                 return Response({"error": "setting.yaml 配置文件未找到。"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f).get('ai', {})
            
            api_key = config.get('openai_api_key')
            api_base = config.get('openai_api_base')
            model_name = config.get('model')

            if not all([api_key, api_base, model_name]):
                return Response({"error": "AI配置不完整 (api_key, api_base, model)。"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 2. 初始化Langchain
            llm = ChatOpenAI(
                model_name=model_name,
                openai_api_key=api_key,
                openai_api_base=api_base,
                temperature=0.3
            )

            # 3. 创建提示模板
            prompt_template = PromptTemplate(
                input_variables=["chart_title", "chart_data"],
                template="""
                您是一位专业的数据分析师。请根据以下图表数据，给出一份简洁、深刻的分析报告。
                报告应包括：
                1.  数据的主要趋势和模式。
                2.  任何值得注意的异常点或突变。
                3.  基于数据洞察提出的可行性建议。
                
                如果分析的是员工增长趋势，请着重分析各公司员工增长情况，提出人力资源管理的建议。
                如果分析的是系统资源使用情况，请着重分析系统性能和优化方向。
                如果分析的是各公司员工数量，请着重分析公司规模和部门结构的合理性。
                
                分析应直接、清晰，语言专业且易于理解。

                图表标题: {chart_title}
                图表数据:
                ```json
                {chart_data}
                ```

                您的分析报告:
                """
            )

            # 4. 创建并运行链
            chain = LLMChain(llm=llm, prompt=prompt_template)
            result = chain.run(chart_title=chart_title, chart_data=str(chart_data))

            return Response({"analysis": result})

        except Exception as e:
            logger.error(f"AI分析时发生错误: {traceback.format_exc()}")
            return Response(
                {"error": f"生成AI分析时发生内部错误: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DashboardDataView(APIView):
    """
    API view to get statistics and chart data for the admin dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        owner = request.user
        
        # Get companies owned by the user
        companies = Company.objects.filter(owner=owner)
        company_ids = companies.values_list('id', flat=True)

        # Stats
        user_count = User.objects.filter(company__in=company_ids).count()
        company_count = companies.count()
        department_count = Department.objects.filter(company__in=company_ids).count()

        # User Growth Chart Data (last 7 days for owned companies)
        user_growth = self.get_user_growth_by_company(companies, company_ids)

        data = {
            'stats': {
                'user_count': user_count,
                'company_count': company_count,
                'department_count': department_count,
            },
            'user_growth': user_growth,
            'system_load': self.get_system_load(),
            'company_user_distribution': self.get_company_user_counts_by_department(companies),
        }
        
        return Response(data)

    def get_system_load(self):
        # Mock data for system load. Replace with actual data if available.
        return [
            {'value': random.randint(30, 80), 'name': 'CPU使用率 (%)'},
            {'value': random.randint(40, 90), 'name': '内存使用率 (%)'},
            {'value': random.randint(20, 70), 'name': '磁盘使用率 (%)'},
        ]

    def get_user_growth_by_company(self, companies, company_ids):
        """
        Calculates user growth for each company over the last 7 days.
        """
        today = timezone.now().date()
        dates = [(today - timedelta(days=i)) for i in range(6, -1, -1)]

        user_growth_counts = User.objects.filter(
            company__id__in=company_ids,
            date_joined__date__in=dates
        ).values('company__name', 'date_joined__date').annotate(count=Count('id')).order_by('company__name', 'date_joined__date')

        company_growth_map = {}
        for item in user_growth_counts:
            company_name = item['company__name']
            if company_name not in company_growth_map:
                company_growth_map[company_name] = {d: 0 for d in dates}
            company_growth_map[company_name][item['date_joined__date']] = item['count']

        for company in companies:
            if company.name not in company_growth_map:
                company_growth_map[company.name] = {d: 0 for d in dates}

        series = []
        for company_name, growth_data in sorted(company_growth_map.items()):
            series.append({
                'name': company_name,
                'type': 'line',
                'data': [growth_data.get(d, 0) for d in dates]
            })

        return {
            'dates': [d.strftime('%Y-%m-%d') for d in dates],
            'series': series
        }

    def get_company_user_counts_by_department(self, companies):
        """
        Calculates user counts for each company, broken down by department.
        """
        companies = companies.prefetch_related('departments', 'users').order_by('name')
        
        all_departments_q = Department.objects.filter(company__in=companies).values_list('name', flat=True).distinct()
        all_department_names = sorted(list(all_departments_q))
        
        series_names = all_department_names + ['其它']
        
        series_data = {name: [] for name in series_names}
        
        company_labels = []
        company_totals = []

        for company in companies:
            company_labels.append(company.name)
            
            department_counts = (
                User.objects.filter(company=company)
                .values(department_name=F('department__name'))
                .annotate(count=Count('id'))
                .values('department_name', 'count')
            )
            
            counts_map = {item['department_name']: item['count'] for item in department_counts}
            
            for dept_name in all_department_names:
                count = counts_map.get(dept_name, 0)
                series_data[dept_name].append(count)

            other_count = counts_map.get(None, 0)
            series_data['其它'].append(other_count)
            
            total_users_in_company = sum(counts_map.values())
            company_totals.append(total_users_in_company)

        final_series = []
        for name, data in series_data.items():
            if any(d > 0 for d in data):
                final_series.append({
                    "name": name,
                    "type": "bar",
                    "stack": "total",
                    "emphasis": {"focus": "series"},
                    "data": data,
                })

        return {
            "labels": company_labels,
            "series": final_series,
            "totals": company_totals,
        }

class AdminUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users in the admin panel, scoped to the owner's companies.
    """
    serializer_class = UserAdminSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'name', 'company__name', 'department__name']

    def get_queryset(self):
        """
        Restricts the returned users to those belonging to companies owned by the logged-in user.
        """
        owner = self.request.user
        company_ids = Company.objects.filter(owner=owner).values_list('id', flat=True)
        return User.objects.filter(company__id__in=company_ids).order_by('-date_joined')

    def perform_create(self, serializer):
        password = self.request.data.get('password')
        user = serializer.save(is_staff=False)
        if password:
            user.set_password(password)
            user.save()

    def perform_update(self, serializer):
        # When updating a user, optionally update password
        password = self.request.data.get('password')
        # Ensure is_staff is not accidentally changed
        user = serializer.save(is_staff=serializer.instance.is_staff)
        if password:
            user.set_password(password)
            user.save()

    def list(self, request, *args, **kwargs):
        if request.query_params.get('all') == 'true':
            queryset = self.get_queryset()
            
            # Filter by company if company_id is provided
            company_id = request.query_params.get('company_id')
            if company_id:
                queryset = queryset.filter(company_id=company_id)
                
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        
        return super().list(request, *args, **kwargs)

class AdminCompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing companies owned by the logged-in user.
    """
    serializer_class = CompanyAdminSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'industry', 'address']

    def get_queryset(self):
        """
        This view should return a list of all the companies
        for the currently authenticated user.
        """
        return Company.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        # Assign the current user as the owner of the new company
        serializer.save(owner=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # Support `all=true` parameter to return all companies without pagination
        if request.query_params.get('all') == 'true':
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class AdminDepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing departments within companies owned by the logged-in user.
    """
    serializer_class = DepartmentAdminSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'company__name', 'manager__name']

    def get_queryset(self):
        """
        This view should return a list of all the departments
        for the currently authenticated user's companies.
        """
        user = self.request.user
        return Department.objects.filter(company__owner=user)

    def perform_create(self, serializer):
        """
        When creating a new department, it is associated with one of the user's companies.
        """
        serializer.save()

    def perform_update(self, serializer):
        with transaction.atomic():
            old_instance = serializer.instance
            new_manager_id = self.request.data.get('manager')

            if new_manager_id is not None:
                try:
                    if new_manager_id == '' or new_manager_id == 'null':
                        new_manager_id = None
                    else:
                        new_manager_id = int(new_manager_id)
                except (ValueError, TypeError):
                    return Response({"detail": "Invalid manager ID."}, status=status.HTTP_400_BAD_REQUEST)

            if 'manager' in self.request.data:
                if old_instance.manager_id != new_manager_id:
                    if old_instance.manager and old_instance.manager.position == "部门主管":
                        old_instance.manager.position = ""
                        old_instance.manager.save()

                    if new_manager_id:
                        try:
                            new_manager = User.objects.get(id=new_manager_id)
                            new_manager.position = "部门主管"
                            new_manager.save()
                        except User.DoesNotExist:
                            return Response({"detail": f"User with ID {new_manager_id} not found."}, status=status.HTTP_404_NOT_FOUND)

            serializer.save()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if request.query_params.get('all') == 'true':
            company_id = request.query_params.get('company')
            if company_id:
                queryset = queryset.filter(company_id=company_id)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class SmartDocAdminViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and managing Documents for the companies owned by the admin user.
    Provides list, retrieve, and destroy actions.
    """
    serializer_class = SmartDocAdminSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'creator__name', 'creator__company__name']

    def get_queryset(self):
        """
        This view should return a list of all the documents
        for all the companies owned by the currently authenticated user.
        """
        owner = self.request.user
        company_ids = Company.objects.filter(owner=owner).values_list('id', flat=True)
        user_ids = User.objects.filter(company__id__in=company_ids).values_list('id', flat=True)
        return Document.objects.filter(creator__id__in=user_ids).order_by('-updated_at')

class ContractAdminViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and managing Contracts for the companies owned by the admin user.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'number', 'company', 'created_by__name', 'created_by__company__name']

    def get_serializer_class(self):
        if self.action == 'list':
            return ContractAdminListSerializer
        return ContractAdminSerializer

    def get_queryset(self):
        """
        This view should return a list of all the contracts
        for all the companies owned by the currently authenticated user.
        """
        owner = self.request.user
        company_ids = Company.objects.filter(owner=owner).values_list('id', flat=True)
        user_ids = User.objects.filter(company__id__in=company_ids).values_list('id', flat=True)
        return Contract.objects.filter(created_by__id__in=user_ids).order_by('-created_at')

class KnowledgeCategoryAdminViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Knowledge Categories owned by the logged-in user's companies.
    """
    serializer_class = KnowledgeCategoryAdminSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        owner = self.request.user
        return KnowledgeCategory.objects.filter(company__owner=owner).order_by('name')

    def perform_create(self, serializer):
        serializer.save()
    
    def list(self, request, *args, **kwargs):
        if request.query_params.get('all') == 'true':
            queryset = self.get_queryset()
            company_id = request.query_params.get('company_id')
            if company_id:
                queryset = queryset.filter(company_id=company_id)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)

class KnowledgeBaseAdminViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Knowledge Base entries owned by the logged-in user's companies.
    """
    serializer_class = KnowledgeBaseAdminSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description', 'category__name', 'company__name']

    def get_queryset(self):
        owner = self.request.user
        return KnowledgeBase.objects.filter(company__owner=owner).order_by('-created_at')

    def perform_create(self, serializer):
        # 序列化器只创建元数据，不保存文件
        instance = serializer.save(creator=self.request.user)
        uploaded_file = self.request.FILES.get('original_file')
        if uploaded_file:
            # 视图负责保存原始文件和处理后的文本文件
            instance.original_filename = uploaded_file.name  # 显式设置原始文件名
            instance.original_file.save(uploaded_file.name, uploaded_file, save=False)
            process_uploaded_file(instance, uploaded_file) # 此方法内部会调用 instance.save()
        else:
            # 理论上由于序列化器验证，不应该到达这里
            instance.save()

    def perform_update(self, serializer):
        # 序列化器只更新实例属性，不执行保存
        instance = serializer.save()
        uploaded_file = self.request.FILES.get('original_file')
        if uploaded_file:
            # 如果有新文件上传，处理并替换
            instance.original_filename = uploaded_file.name  # 显式设置原始文件名
            instance.original_file.save(uploaded_file.name, uploaded_file, save=False)
            process_uploaded_file(instance, uploaded_file) # 此方法内部会调用 instance.save()
        else:
            # 如果没有新文件，仅保存元数据更改
            instance.save()

    def list(self, request, *args, **kwargs):
        if request.query_params.get('all') == 'true':
            queryset = self.get_queryset()
            company_id = request.query_params.get('company_id')
            if company_id:
                queryset = queryset.filter(company_id=company_id)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)

GRAPHRAG_DIR = getattr(settings, 'GRAPHRAG_DIR', os.path.join(settings.BASE_DIR, 'graphrag-main'))
GRAPHRAG_INPUT_DIR = getattr(settings, 'GRAPHRAG_INPUT_DIR', os.path.join(GRAPHRAG_DIR, 'ragtest', 'input'))

class AdminKnowledgeBuildView(APIView):
    """
    处理管理员触发的公司知识库构建
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """获取管理员名下所有公司的知识库构建状态"""
        owner = request.user
        companies = Company.objects.filter(owner=owner)
        
        # 获取所有已有的构建记录
        build_statuses = CompanyKnowledgeBase.objects.filter(company__in=companies)
        status_map = {bs.company_id: bs for bs in build_statuses}
        
        # 重新组织，确保每个公司都有记录，并直接查询文件数量
        results = []
        for company in companies:
            file_count = KnowledgeBase.objects.filter(company=company).count()
            status_obj = status_map.get(company.id)
            
            data = {
                "company_id": company.id,
                "company_name": company.name,
                "file_count": file_count,
            }
            if status_obj:
                data.update({
                    "status": status_obj.status,
                    "last_built_at": status_obj.last_built_at,
                    "processing_message": status_obj.processing_message,
                })
            else:
                data.update({
                    "status": "not_built",
                    "last_built_at": None,
                    "processing_message": "知识库尚未构建",
                })
            results.append(data)
        return Response(results)

    def post(self, request):
        """为指定的一个或多个公司构建知识库"""
        company_ids = request.data.get('company_ids', [])
        if not isinstance(company_ids, list) or not company_ids:
            return Response({"error": "请提供一个包含公司ID的列表。"}, status=status.HTTP_400_BAD_REQUEST)

        owner = request.user
        # 验证所有请求的公司都属于该管理员
        valid_companies = Company.objects.filter(owner=owner, id__in=company_ids)
        if len(valid_companies) != len(set(company_ids)):
             return Response({"error": "包含无效或不属于您的公司ID。"}, status=status.HTTP_403_FORBIDDEN)

        build_requests = []
        skipped_companies = []
        for company in valid_companies:
            # 检查该公司下是否有知识库文件
            if not KnowledgeBase.objects.filter(company=company).exists():
                skipped_companies.append(company.name)
                # 更新状态，告知用户为何无法构建
                CompanyKnowledgeBase.objects.update_or_create(
                    company=company,
                    defaults={
                        'status': 'failed',
                        'triggered_by': owner,
                        'processing_message': '无法构建：该公司下没有任何知识库文件。'
                    }
                )
                continue
            
            # 为每个公司创建或获取 CompanyKnowledgeBase 记录
            company_kb, created = CompanyKnowledgeBase.objects.update_or_create(
                company=company,
                defaults={
                    'status': 'pending',
                    'triggered_by': owner,
                    'processing_message': '已加入构建队列'
                }
            )

            # 启动一个新线程来处理构建任务
            thread = threading.Thread(target=self._build_knowledge_base, args=(company.id, company_kb.id))
            thread.daemon = True
            thread.start()
            build_requests.append(company.name)

        message_parts = []
        if build_requests:
            message_parts.append(f"已为公司 {', '.join(build_requests)} 启动构建任务。")
        if skipped_companies:
            message_parts.append(f"公司 {', '.join(skipped_companies)} 因没有文件而被跳过。")
        
        final_message = " ".join(message_parts)
        if not final_message:
            final_message = "没有可启动构建任务的公司。"

        return Response({
            "message": final_message
        }, status=status.HTTP_202_ACCEPTED)

    def _build_knowledge_base(self, company_id, company_kb_id):
        company_kb = CompanyKnowledgeBase.objects.get(id=company_kb_id)
        try:
            self._update_build_status(company_kb_id, company_id, 'processing', '开始构建流程...')

            # 清理旧的输出和索引目录以确保全新构建
            output_dir = os.path.join(GRAPHRAG_DIR, 'ragtest', 'output', f'company_{company_id}')
            index_dir = os.path.join(GRAPHRAG_DIR, 'ragtest', 'index', f'company_{company_id}')
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
                logger.info(f"已清理旧的输出目录: {output_dir}")
            if os.path.exists(index_dir):
                shutil.rmtree(index_dir)
                logger.info(f"已清理旧的索引目录: {index_dir}")
            
            # 1. 创建配置文件
            config_path = self._create_company_config(company_id, GRAPHRAG_DIR)
            
            # 2. 执行 GraphRAG 命令
            env = self._get_subprocess_env()
            cmd = [
                "python", "-m", "graphrag", "index",
                "--root", GRAPHRAG_DIR,
                "--config", config_path
            ]
            cmd_str = " ".join(cmd)
            self._update_build_status(company_kb_id, company_id, 'processing', f'正在执行命令: {cmd_str}')
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', env=env, cwd=GRAPHRAG_DIR)
            stdout, stderr = process.communicate()
            
            # 3. 处理结果
            self._handle_build_result(company_kb, company_id, process.returncode, stdout, stderr, cmd_str)

        except Exception as e:
            logger.error(f"知识库构建线程异常 (Company ID: {company_id}): {traceback.format_exc()}")
            self._update_build_status(company_kb_id, company_id, 'failed', f"构建时发生内部错误: {e}")

    def _create_company_config(self, company_id, graphrag_dir):
        """
        通过读取基础模板并注入公司特定路径，为公司创建 GraphRAG 配置文件。
        这确保了所有必要的模型配置都被包含在内。
        """
        base_config_path = os.path.join(graphrag_dir, "ragtest", "settings.yaml")
        if not os.path.exists(base_config_path):
            raise FileNotFoundError(f"基础配置文件未找到: {base_config_path}")

        with open(base_config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # 定义公司特定的路径
        company_output_dir = os.path.join(graphrag_dir, "ragtest", "output", f"company_{company_id}")
        company_input_dir = os.path.join(graphrag_dir, "ragtest", "input", f"company_{company_id}")
        company_cache_dir = os.path.join(graphrag_dir, "ragtest", "cache", f"company_{company_id}")
        company_index_dir = os.path.join(graphrag_dir, "ragtest", "index", f"company_{company_id}")

        # 更新配置字典中的路径
        if 'output' in config_data:
            config_data['output']['base_dir'] = company_output_dir
        if 'input' in config_data:
            config_data['input']['base_dir'] = company_input_dir
        if 'cache' in config_data:
            config_data['cache']['base_dir'] = company_cache_dir
        
        # 确保为每个公司隔离向量存储
        if 'vector_store' in config_data and 'default_vector_store' in config_data['vector_store']:
            config_data['vector_store']['default_vector_store']['db_uri'] = company_index_dir

        # 确保模型配置中的参数设置正确
        if "models" in config_data:
            for model_id in config_data["models"]:
                if "tokens_per_minute" in config_data["models"][model_id]:
                    config_data["models"][model_id]["tokens_per_minute"] = 50000
                if "requests_per_minute" in config_data["models"][model_id]:
                    config_data["models"][model_id]["requests_per_minute"] = 1000
                else:
                    # 如果不存在，添加该参数
                    config_data["models"][model_id]["requests_per_minute"] = 1000

        # 确保输出目录存在
        os.makedirs(company_output_dir, exist_ok=True)
        os.makedirs(company_input_dir, exist_ok=True)
        os.makedirs(company_cache_dir, exist_ok=True)
        os.makedirs(company_index_dir, exist_ok=True)
        
        # 定义新配置文件的保存路径，确保它直接位于 ragtest 目录下
        new_config_path = os.path.join(graphrag_dir, "ragtest", f"config_company_{company_id}.yml")

        with open(new_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True)

        return new_config_path

    def _get_subprocess_env(self):
        env = os.environ.copy()
        # 强制子进程使用UTF-8编码，解决Windows下的编码问题
        env['PYTHONIOENCODING'] = 'utf-8'
        
        dotenv_path = os.path.join(GRAPHRAG_DIR, '.env')
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path=dotenv_path, override=True)
            # 更新环境变量
            for key, value in dict(os.environ).items():
                if key.startswith("GRAPHRAG_") or key.startswith("OPENAI_"):
                    env[key] = value
        return env

    def _handle_build_result(self, company_kb, company_id, return_code, stdout, stderr, cmd_str):
        # Ensure stdout and stderr are strings before processing
        stdout_str = stdout or ""
        stderr_str = stderr or ""
        
        if return_code == 0:
            final_message = f"构建成功完成。\nOutput:\n{stdout_str[-1000:]}"
            # 将状态更新和时间戳更新合并为一次原子操作
            CompanyKnowledgeBase.objects.filter(id=company_kb.id).update(
                status='completed',
                processing_message=final_message,
                last_built_at=timezone.now()
            )
        else:
            final_message = f"构建失败 (代码: {return_code})。\nCommand: {cmd_str}\nError:\n{stderr_str[-2000:]}"
            self._update_build_status(company_kb.id, company_id, 'failed', final_message)

    def _update_build_status(self, company_kb_id, company_id, status, message, cmd=None, code=None, output=None):
        try:
            CompanyKnowledgeBase.objects.filter(id=company_kb_id).update(
                status=status,
                processing_message=message
            )
        except CompanyKnowledgeBase.DoesNotExist:
             logger.error(f"尝试更新不存在的构建记录: {company_kb_id}") 

class AdminContractTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing contract templates by the admin.
    """
    serializer_class = ContractTemplateAdminSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'contract_type', 'industry', 'scene']

    def get_queryset(self):
        """
        Admins can see all contract templates.
        """
        return ContractTemplate.objects.all()

    def perform_create(self, serializer):
        """
        Set the creator to the current user upon creation.
        """
        serializer.save(created_by=self.request.user) 