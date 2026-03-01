"""Views for the knowledge app."""

import os
import logging
import uuid
import shutil
import json
import subprocess
from django.conf import settings
from django.db import transaction, models
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, FileResponse, StreamingHttpResponse
from rest_framework import viewsets, status, permissions, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from .models import KnowledgeCategory, KnowledgeBase, KnowledgeChunk, CompanyKnowledgeBase
from .serializers import (
    KnowledgeCategorySerializer,
    KnowledgeBaseSerializer,
    KnowledgeBaseDetailSerializer,
    KnowledgeBaseUploadSerializer,
    KnowledgeChunkSerializer
)
from datetime import datetime
import threading
import traceback
from django.utils.text import slugify
from django.core.files.base import ContentFile
import io
import hashlib
from apps.users.models import Company
import tempfile
import yaml
from dotenv import load_dotenv
import re
from apps.ai.services import LangChainAssistant
from django.core.files import File
from apps.ai.models import AIChat, AIChatMessage  # 添加导入AIChat和AIChatMessage模型
import pandas as pd  # 添加pandas导入用于处理parquet文件
import math  # 添加math模块用于处理浮点数

# 设置日志
logger = logging.getLogger(__name__)

# 配置更详细的GraphRAG日志
graphrag_logger = logging.getLogger('graphrag')
graphrag_logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
graphrag_logger.addHandler(console_handler)
graphrag_logger.propagate = True

# 定义graphrag输入目录路径
GRAPHRAG_INPUT_DIR = getattr(settings, 'GRAPHRAG_INPUT_DIR', os.path.join(
    settings.BASE_DIR, 'graphrag-main', 'ragtest', 'input'))

# 确保目录存在
os.makedirs(GRAPHRAG_INPUT_DIR, exist_ok=True)


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

# 导入文件处理相关库并分别检查每个库的可用性
HAS_PDF_LIB = False
try:
    import pypdf  # 替代PyMuPDF
    HAS_PDF_LIB = True
except ImportError:
    logger.warning("pypdf 库未安装，无法处理PDF文件。请执行: pip install pypdf")

HAS_DOCX_LIB = False
try:
    import docx  # python-docx
    HAS_DOCX_LIB = True
except ImportError:
    logger.warning("python-docx 库未安装，无法处理DOCX文件。请执行: pip install python-docx")

HAS_TEXTRACT_LIB = False
try:
    import textract
    HAS_TEXTRACT_LIB = True
except ImportError:
    logger.warning("textract 库未安装，部分文件类型可能无法处理。请执行: pip install textract")


def extract_text_from_pdf(file_path):
    """从PDF文件中提取文本"""
    if not HAS_PDF_LIB:
        return "系统未安装必要的库，无法处理PDF文件。请执行: pip install pypdf"
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf = pypdf.PdfReader(file)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        return text
    except Exception as e:
        logger.error(f"PDF文本提取失败: {e}")
        return f"文件处理错误: {e}"


def extract_text_from_doc(file_path):
    """从Word文档中提取文本"""
    if not HAS_DOCX_LIB and not HAS_TEXTRACT_LIB:
        return "系统未安装必要的库，无法处理Word文档。"
    try:
        if file_path.endswith('.docx') and HAS_DOCX_LIB:
            doc = docx.Document(file_path)
            return "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        elif HAS_TEXTRACT_LIB:
            return textract.process(file_path).decode('utf-8', errors='replace')
        return ""
    except Exception as e:
        logger.error(f"Word文档文本提取失败: {e}")
        return f"文件处理错误: {e}"


def copy_text_file(file_path):
    """复制文本文件内容，处理不同编码"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        logger.error(f"文本文件读取失败: {e}")
        return f"文件处理错误: {e}"

def extract_text_from_ppt(file_path):
    """从PPT文件中提取文本"""
    if not HAS_TEXTRACT_LIB:
        return "系统未安装textract库，无法处理PPT文件。请执行: pip install textract"
    try:
        return textract.process(file_path).decode('utf-8', errors='replace')
    except Exception as e:
        logger.error(f"PPT文本提取失败: {e}")
        return f"文件处理错误: {e}"

def extract_text_from_excel(file_path):
    """从Excel文件中提取文本"""
    if not HAS_TEXTRACT_LIB:
        return "系统未安装textract库，无法处理Excel文件。请执行: pip install textract"
    try:
        return textract.process(file_path).decode('utf-8', errors='replace')
    except Exception as e:
        logger.error(f"Excel文本提取失败: {e}")
        return f"文件处理错误: {e}"

def is_gibberish(text, threshold=0.3):
    """一个简单的乱码检测函数（可以根据需要改进）"""
    if not text or len(text) < 100:
        return False
    import re
    # 乱码通常包含大量连续的非字母数字字符或不常见的unicode字符
    non_alnum = len(re.findall(r'[^a-zA-Z0-9\s\u4e00-\u9fa5,.!?]', text))
    ratio = non_alnum / len(text)
    return ratio > threshold


class KnowledgeCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing knowledge categories."""
    queryset = KnowledgeCategory.objects.all()
    serializer_class = KnowledgeCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_company = self.request.user.company
        query = models.Q(creator=self.request.user) | models.Q(creator__isnull=True)
        if user_company:
            company_creators = user_company.users.all()
            query |= models.Q(creator__in=company_creators)
        return KnowledgeCategory.objects.filter(query).order_by('name')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


# 定义知识库分页类
class KnowledgeBasePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing knowledge base documents."""
    queryset = KnowledgeBase.objects.all()
    serializer_class = KnowledgeBaseSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    pagination_class = KnowledgeBasePagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return KnowledgeBaseDetailSerializer
        elif self.action in ['create', 'upload']:
            return KnowledgeBaseUploadSerializer
        return KnowledgeBaseSerializer

    def get_queryset(self):
        queryset = KnowledgeBase.objects.all()
        user_company = self.request.user.company
        if user_company:
            queryset = queryset.filter(company=user_company)
        else:
            queryset = queryset.filter(creator=self.request.user)

        # 文档分类筛选
        category_id = self.request.query_params.get('category')
        if category_id and category_id.lower() != 'all':
            queryset = queryset.filter(category_id=category_id)
        
        # 搜索功能
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) |
                models.Q(description__icontains=search)
            )
            
        # 文件类型筛选
        file_type = self.request.query_params.get('file_type')
        if file_type:
            file_types = [ft.strip() for ft in file_type.split(',') if ft.strip()]
            if file_types:
                type_query = models.Q()
                for ft in file_types:
                    # 构建OR查询，同时检查metadata中的file_type和原始文件名的后缀
                    type_query |= models.Q(metadata__file_type=ft)
                    type_query |= models.Q(original_filename__iendswith=f'.{ft}')
                
                queryset = queryset.filter(type_query)
            
        # 创建日期筛选
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
            
        # 文档状态筛选
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        else:
            # 默认排除失败的文档
            exclude_status = self.request.query_params.get('exclude_status', 'failed')
            if exclude_status and exclude_status.lower() != 'none':
                exclude_statuses = exclude_status.split(',')
                queryset = queryset.exclude(status__in=exclude_statuses)
        
        return queryset.order_by('-created_at')

    def destroy(self, request, *args, **kwargs):
        """
        删除知识库文件，同时删除后端的原始文件和转换后的文件
        """
        instance = self.get_object()
        logger.info(f"开始删除知识库文件: ID={instance.id}, 标题={instance.title}")
        
        # 1. 记录需要删除的文件路径信息
        original_file_path = None
        converted_file_path = None
        
        # 获取原始文件路径
        if instance.original_file:
            original_file_path = instance.original_file.path
            logger.info(f"原始文件路径: {original_file_path}")
        
        # 获取转换后的文件路径
        if instance.file:
            converted_file_path = instance.file.path
            logger.info(f"转换后的文件路径: {converted_file_path}")
        
        # 2. 检查并删除GraphRAG输入目录中的文件
        if instance.company:
            company_id = instance.company.id
            # 构建可能的GraphRAG输入目录路径
            input_dir = os.path.join(GRAPHRAG_INPUT_DIR, f"company_{company_id}")
            
            if os.path.exists(input_dir):
                # 尝试找到与此文档相关的文件
                if instance.original_filename:
                    base_name = os.path.splitext(instance.original_filename)[0]
                    # 查找可能匹配的文件
                    for file_name in os.listdir(input_dir):
                        # 检查文件名是否包含基本名称或文档ID
                        if (base_name.lower() in file_name.lower() or 
                            str(instance.id) in file_name):
                            file_path = os.path.join(input_dir, file_name)
                            try:
                                if os.path.isfile(file_path):
                                    os.remove(file_path)
                                    logger.info(f"已删除GraphRAG输入文件: {file_path}")
                            except Exception as e:
                                logger.error(f"删除GraphRAG输入文件失败: {file_path}, 错误: {e}")
        
        # 3. 执行模型实例删除操作
        response = super().destroy(request, *args, **kwargs)
        
        # 4. 删除模型实例后，检查并删除物理文件
        try:
            # 删除原始文件
            if original_file_path and os.path.exists(original_file_path):
                os.remove(original_file_path)
                logger.info(f"已删除原始文件: {original_file_path}")
            
            # 删除转换后的文件
            if converted_file_path and os.path.exists(converted_file_path):
                os.remove(converted_file_path)
                logger.info(f"已删除转换后的文件: {converted_file_path}")
                
            # 尝试删除可能的父目录（如果为空）
            for path in [original_file_path, converted_file_path]:
                if path:
                    try:
                        # 获取父目录
                        parent_dir = os.path.dirname(path)
                        # 如果父目录为空，则删除
                        if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                            os.rmdir(parent_dir)
                            logger.info(f"已删除空目录: {parent_dir}")
                    except Exception as e:
                        logger.warning(f"尝试删除空目录时出错: {e}")
                        
        except Exception as e:
            logger.error(f"删除物理文件时出错: {e}")
            # 不影响API响应，仅记录错误
        
        return response

    @transaction.atomic
    def perform_create(self, serializer):
        uploaded_file = self.request.FILES.get('file')
        if not uploaded_file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        # 创建一个可修改的数据副本，并移除文件字段，防止序列化器自动处理
        request_data = self.request.data.copy()
        request_data.pop('file', None)
        
        # 使用修改后的数据重新初始化或验证序列化器
        # 注意：这里的 'serializer' 是DRF框架传入的，最好用新的变量
        local_serializer = self.get_serializer(data=request_data)
        local_serializer.is_valid(raise_exception=True)

        company = self.request.user.company
        if not company:
            return Response({'error': 'User is not associated with a company'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. 检查文件内容是否重复
        file_content = uploaded_file.read()
        uploaded_file.seek(0)
        
        if not file_content:
            return Response({'error': 'Uploaded file is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        file_hash = hashlib.md5(file_content).hexdigest()
        
        existing_doc = KnowledgeBase.objects.filter(metadata__file_hash=file_hash, company=company).first()
        if existing_doc:
            return Response({
                'status': 'existed',
                'message': '相同内容的文件已存在',
                'document_id': existing_doc.id
            }, status=status.HTTP_409_CONFLICT)
        
        # 2. 将上传的文件保存到临时文件以便提取内容
        original_filename = uploaded_file.name
        file_ext = os.path.splitext(original_filename)[1].lower().replace('.', '')
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as temp_f:
            temp_f.write(file_content)
            temp_file_path = temp_f.name

        text_content = ""
        try:
            # 3. 根据文件类型提取文本
            method_name = SUPPORTED_FILE_TYPES.get(file_ext)
            if not method_name:
                raise ValueError(f"不支持的文件类型: {file_ext}")
            
            extraction_method = globals().get(method_name)
            text_content = extraction_method(temp_file_path)

            if not text_content or text_content.startswith("文件处理错误") or is_gibberish(text_content):
                raise ValueError("文本提取失败或内容可能为乱码")

            # 4. 使用 local_serializer 创建并保存KnowledgeBase实例
            knowledge = local_serializer.save(
                creator=self.request.user,
                company=company,
                status='processing', # 初始状态
                original_filename=original_filename,
                metadata={'file_hash': file_hash, 'source': 'file_upload', 'file_type': file_ext}
            )

            # 保存原始文件
            uploaded_file.seek(0)  # 重置文件指针
            knowledge.original_file.save(original_filename, uploaded_file, save=False)

            # 5. 将提取的文本保存到 'file' 字段
            company_subdir = f"company_{company.id}"
            safe_base_name = slugify(os.path.splitext(original_filename)[0])
            txt_filename = f"{safe_base_name}_{file_hash[:8]}.txt"
            rel_path = os.path.join(company_subdir, txt_filename)
            
            knowledge.file.save(rel_path, ContentFile(text_content.encode('utf-8')), save=False)

            # 6. 更新状态为完成
            knowledge.status = 'completed'
            knowledge.processing_message = f"文件处理完成，已生成: {knowledge.file.name}"
            knowledge.save() # 保存所有更改

            serializer = self.get_serializer(knowledge)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"处理上传文件失败: {e}", exc_info=True)
            # 如果发生错误，且knowledge对象已创建，则标记为失败
            if 'knowledge' in locals() and knowledge.pk:
                knowledge.status = 'failed'
                knowledge.processing_message = f"处理失败: {str(e)}"
                knowledge.save(update_fields=['status', 'processing_message'])
            return Response({'error': f"处理文件时出错: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            # 7. 清理临时文件
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)


class KnowledgeChunkViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing document chunks."""
    queryset = KnowledgeChunk.objects.all()
    serializer_class = KnowledgeChunkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_company = self.request.user.company
        if user_company:
            return KnowledgeChunk.objects.filter(knowledge_base__company=user_company)
        return KnowledgeChunk.objects.none()


# 全局构建状态存储
build_status_store = {}

class KnowledgeBaseBuildView(APIView):
    """处理知识库构建的视图"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """开始知识库构建过程"""
        company_id = request.user.company_id
        if not company_id:
            return Response({"error": "用户没有关联公司"}, status=status.HTTP_400_BAD_REQUEST)

        # 检查是否已有构建任务在进行，如果有，取消它们
        stale_builds = CompanyKnowledgeBase.objects.filter(company_id=company_id, status__in=['processing', 'pending'])
        if stale_builds.exists():
            for build in stale_builds:
                build.status = 'cancelled'
                log_message = f"[{datetime.now()}] New build requested, cancelling this one."
                build.processing_message = log_message
                
                # 确保metadata字段是字典类型
                if not isinstance(build.metadata, dict):
                    build.metadata = {}
                
                # 将日志信息添加到metadata中
                if 'logs' not in build.metadata:
                    build.metadata['logs'] = []
                build.metadata['logs'].append(log_message)
                
                build.save()

        # 创建一个新的公司知识库构建记录
        company_kb = CompanyKnowledgeBase.objects.create(
            company_id=company_id,
            status='pending',
            triggered_by=request.user
        )

        # 启动后台线程进行构建
        thread = threading.Thread(target=self._build_knowledge_base, args=(company_id, company_kb.id))
        thread.daemon = True
        thread.start()

        return Response({
            "message": "知识库构建任务已启动",
            "build_id": company_kb.id
        }, status=status.HTTP_202_ACCEPTED)

    def get(self, request):
        """获取最新知识库构建状态"""
        user_company = request.user.company
        if not user_company:
            return Response({'status': 'not_started', 'message': '用户未关联任何公司'})
            
        company_id = str(user_company.id)
        
        try:
            # 使用 filter() 和 latest() 避免 MultipleObjectsReturned 错误
            company_kb = CompanyKnowledgeBase.objects.filter(company=user_company).latest('updated_at')
            response_data = {
                'status': company_kb.status,
                'message': company_kb.processing_message,
                'last_built_at': company_kb.last_built_at.isoformat() if company_kb.last_built_at else None,
            }
            # 检查内存中的状态存储
            if company_id in build_status_store and build_status_store[company_id].get('status') == 'processing':
                mem_status = build_status_store[company_id]
                response_data.update({
                    'progress': mem_status.get('progress', 0),
                    'graphrag_output': mem_status.get('graphrag_output', '')
                })
            return Response(response_data)
        except CompanyKnowledgeBase.DoesNotExist:
            return Response({'status': 'not_started', 'message': '该公司知识库构建尚未开始'})

    def _build_knowledge_base(self, company_id, company_kb_id):
        # 初始化内存状态存储
        build_status_store[str(company_id)] = {
            'status': 'processing', 'progress': 0, 'message': '正在准备...',
            'started_at': datetime.now().isoformat(), 'company_id': str(company_id),
            'graphrag_output': ''
        }
        
        try:
            # 确保获取的是最新的记录
            company_kb = CompanyKnowledgeBase.objects.filter(id=company_kb_id).latest('updated_at')
            company_kb.status = 'processing'
            company_kb.processing_message = '开始构建流程...'
            company_kb.save()

            graphrag_dir = os.path.join(settings.BASE_DIR, 'graphrag-main')
            if not os.path.exists(graphrag_dir):
                error_msg = f'GraphRAG目录不存在: {graphrag_dir}'
                logger.error(error_msg)
                graphrag_logger.error(error_msg)
                self._update_build_status(company_kb_id, str(company_id), 'failed', error_msg)
                return

            # 清理旧的输出和索引目录以确保全新构建
            output_dir = os.path.join(graphrag_dir, 'ragtest', 'output', f'company_{company_id}')
            index_dir = os.path.join(graphrag_dir, 'ragtest', 'index', f'company_{company_id}')
            
            build_status_store[str(company_id)].update({'progress': 10, 'message': '清理旧索引...'})
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
                logger.info(f"已清理旧的输出目录: {output_dir}")
                graphrag_logger.info(f"已清理旧的输出目录: {output_dir}")
            if os.path.exists(index_dir):
                shutil.rmtree(index_dir)
                logger.info(f"已清理旧的索引目录: {index_dir}")
                graphrag_logger.info(f"已清理旧的索引目录: {index_dir}")
            
            # 重建空目录，确保GraphRAG有写入的目标
            os.makedirs(output_dir, exist_ok=True)
            os.makedirs(index_dir, exist_ok=True)
            logger.info(f"已重新创建空的输出和索引目录")
            graphrag_logger.info(f"已重新创建空的输出和索引目录")

            # 动态创建公司专属配置文件
            try:
                config_data = self._create_company_config(company_id, graphrag_dir)
                config_file_path = os.path.join(graphrag_dir, 'ragtest', f'company_{company_id}_config.yaml')
                with open(config_file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, allow_unicode=True, sort_keys=False)
                build_status_store[str(company_id)].update({'progress': 20, 'message': '已创建配置...'})
            except Exception as e:
                error_msg = f'创建配置文件失败: {str(e)}'
                logger.error(error_msg)
                graphrag_logger.error(error_msg, exc_info=True)
                self._update_build_status(company_kb_id, str(company_id), 'failed', error_msg)
                return
            
            # 准备环境变量
            try:
                env = self._get_subprocess_env()
            except ValueError as e:
                error_msg = f'环境配置错误: {str(e)}'
                logger.error(error_msg)
                graphrag_logger.error(error_msg)
                self._update_build_status(company_kb_id, str(company_id), 'failed', error_msg)
                return
            
            build_status_store[str(company_id)].update({'progress': 30, 'message': '正在执行GraphRAG索引...'})
            company_kb.processing_message = '正在执行GraphRAG索引...'
            company_kb.save(update_fields=['processing_message'])
            
            # 运行GraphRAG index命令
            cmd_args = ["python", "-u", "-m", "graphrag", "index", "--config", os.path.relpath(config_file_path, graphrag_dir), "--verbose"]
            cmd_str = " ".join(cmd_args)
            graphrag_logger.info(f"执行GraphRAG构建命令: {cmd_str}")
            graphrag_logger.info(f"配置文件: {os.path.relpath(config_file_path, graphrag_dir)}")
            graphrag_logger.info(f"工作目录: {graphrag_dir}")

            # 设置子进程以实时获取输出，移除text参数
            process = subprocess.Popen(
                cmd_args,
                cwd=graphrag_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1
            )

            # 读取实时输出并记录日志
            stdout_text = ""
            stderr_text = ""

            # 创建线程读取输出
            def read_output(pipe, is_error):
                nonlocal stdout_text, stderr_text
                try:
                    reader = io.TextIOWrapper(pipe, encoding='utf-8', errors='replace')
                    for line in iter(reader.readline, ''):
                        if is_error:
                            stderr_text += line
                            graphrag_logger.debug(f"GraphRAG构建stderr: {line.strip()}")
                        else:
                            stdout_text += line
                            graphrag_logger.debug(f"GraphRAG构建stdout: {line.strip()}")
                            # 基于输出更新进度
                            if "Processing documents" in line:
                                build_status_store[str(company_id)].update({'progress': 40, 'message': '处理文档中...'})
                            elif "Building embeddings" in line:
                                build_status_store[str(company_id)].update({'progress': 60, 'message': '构建嵌入向量...'})
                            elif "Building graph" in line:
                                build_status_store[str(company_id)].update({'progress': 80, 'message': '构建知识图谱...'})
                except Exception as e:
                    if is_error:
                        graphrag_logger.error(f"读取stderr出错: {e}")
                    else:
                        graphrag_logger.error(f"读取stdout出错: {e}")
                finally:
                    # 确保管道关闭
                    try:
                        pipe.close()
                    except Exception:
                        pass
                
            # 启动线程
            stdout_thread = threading.Thread(target=read_output, args=(process.stdout, False))
            stderr_thread = threading.Thread(target=read_output, args=(process.stderr, True))
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()
            
            # 等待进程完成
            graphrag_logger.info("等待GraphRAG构建进程完成...")
            return_code = process.wait()
            
            # 确保线程结束
            stdout_thread.join()
            stderr_thread.join()
            
            graphrag_logger.info(f"GraphRAG构建进程结束，返回码: {return_code}")
            
            # 处理构建结果
            self._handle_build_result(company_kb, company_id, return_code, stdout_text, stderr_text, cmd_str)
            
        except Exception as e:
            error_msg = f'构建知识库时发生错误: {str(e)}'
            logger.error(f'{error_msg}\n{traceback.format_exc()}')
            graphrag_logger.error(error_msg, exc_info=True)
            self._update_build_status(company_kb_id, str(company_id), 'failed', error_msg)

    def _create_company_config(self, company_id, graphrag_dir):
        base_config_path = os.path.join(graphrag_dir, 'ragtest', 'settings.yaml')
        with open(base_config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        config_data['input']['base_dir'] = f"./ragtest/input/company_{company_id}"
        config_data['output']['base_dir'] = f"./ragtest/output/company_{company_id}"
        if config_data.get("vector_store", {}).get("default_vector_store"):
            config_data["vector_store"]["default_vector_store"]["db_uri"] = f"./ragtest/index/company_{company_id}"
        
        # 确保模型配置存在，并设置参数为整数值
        if "models" in config_data:
            for model_id in config_data["models"]:
                if "tokens_per_minute" in config_data["models"][model_id]:
                    config_data["models"][model_id]["tokens_per_minute"] = 50000
                if "requests_per_minute" in config_data["models"][model_id]:
                    config_data["models"][model_id]["requests_per_minute"] = 1000
                else:
                    # 如果不存在，添加该参数
                    config_data["models"][model_id]["requests_per_minute"] = 1000
        
        return config_data

    def _get_subprocess_env(self):
        # 指定.env文件的路径
        dotenv_path = os.path.join(settings.BASE_DIR, 'graphrag-main', 'ragtest', '.env')
        
        # 如果.env文件存在，则加载它
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path=dotenv_path)
            logger.info(f"已成功从 {dotenv_path} 加载 .env 文件")
        else:
            logger.warning(f"在路径 {dotenv_path} 未找到 .env 文件，将仅依赖现有环境变量")

        env = os.environ.copy()
        env["PYTHONPATH"] = str(settings.BASE_DIR)
        env["PYTHONIOENCODING"] = "utf-8"
        api_key = getattr(settings, 'GRAPHRAG_API_KEY', os.getenv('GRAPHRAG_API_KEY'))
        if not api_key:
            logger.error("GRAPHRAG_API_KEY 在 Django 设置或环境变量中均未找到。")
            raise ValueError("GRAPHRAG_API_KEY 未配置")
        env['GRAPHRAG_API_KEY'] = api_key
        return env

    def _handle_build_result(self, company_kb, company_id, return_code, stdout, stderr, cmd_str):
        full_output = f"--- STDOUT ---\n{stdout}\n\n--- STDERR ---\n{stderr}"
        if return_code != 0:
            logger.error(f"GraphRAG为公司 {company_id} 执行失败，返回码: {return_code}。\n{full_output}")
            graphrag_logger.error(f"GraphRAG为公司 {company_id} 执行失败，返回码: {return_code}")
            graphrag_logger.error(f"GraphRAG失败STDOUT: {stdout}")
            graphrag_logger.error(f"GraphRAG失败STDERR: {stderr}")
            status, message = 'failed', f'构建失败。错误: {stderr[:500]}'
            build_status_store[str(company_id)].update({'progress': 100})
        else:
            logger.info(f"GraphRAG为公司 {company_id} 执行成功。")
            logger.info(f"GraphRAG为公司 {company_id} 构建日志详情:\n{full_output}")
            graphrag_logger.info(f"GraphRAG为公司 {company_id} 执行成功")
            graphrag_logger.info(f"GraphRAG构建完成，输出摘要:")
            
            # 尝试从输出中提取关键信息
            if "Documents processed" in stdout:
                for line in stdout.split('\n'):
                    if any(key in line for key in ["Documents processed", "Chunks created", "Embeddings", "Connections"]):
                        graphrag_logger.info(f"  {line.strip()}")
            
            status, message = 'completed', '知识库构建完成。'
            build_status_store[str(company_id)].update({'progress': 100})
        
        self._update_build_status(company_kb.id, str(company_id), status, message, cmd_str, return_code, full_output)

    def _update_build_status(self, company_kb_id, company_id, status, message, cmd=None, code=None, output=None):
        if company_id in build_status_store:
            build_status_store[company_id].update({'status': status, 'message': message})
        try:
            company_kb = CompanyKnowledgeBase.objects.get(id=company_kb_id)
            company_kb.status = status
            company_kb.processing_message = message
            if status == 'completed':
                company_kb.last_built_at = datetime.now()
            if cmd:
                 company_kb.metadata = {'command': cmd, 'return_code': code, 'log': output, 'finished_at': datetime.now().isoformat()}
            company_kb.save()
        except CompanyKnowledgeBase.DoesNotExist:
            logger.error(f"更新构建状态时找不到公司知识库记录 (ID: {company_kb_id})")


class GraphRAGQueryView(APIView):
    """处理GraphRAG查询的视图"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        query_text = request.data.get('query') or request.data.get('message')
        method = request.data.get('method', 'local')
        chat_id = request.data.get('chat_id')  # 获取聊天ID（如果有）

        if not query_text:
            return Response({'status': 'error', 'message': '必须在请求中提供 "query" 或 "message" 字段。'}, status=status.HTTP_400_BAD_REQUEST)
        
        if method not in ['local', 'basic']:
             return Response({'status': 'error', 'message': '无效的搜索方法'}, status=status.HTTP_400_BAD_REQUEST)

        user_company = request.user.company
        if not user_company:
            return Response({'status': 'error', 'message': '用户未关联任何公司'}, status=status.HTTP_400_BAD_REQUEST)
    
        try:
            # 获取或创建聊天会话
            if chat_id:
                try:
                    chat = AIChat.objects.get(id=chat_id, user=request.user)
                except AIChat.DoesNotExist:
                    return Response({"error": "Chat not found."}, status=status.HTTP_404_NOT_FOUND)
            else:
                chat = AIChat.objects.create(user=request.user, title=query_text[:50] or "新知识库对话")
            
            # 保存用户消息
            user_message = AIChatMessage.objects.create(
                chat=chat,
                role='user',
                content=query_text,
                source='knowledge_base'
            )
            
            # 确保知识库存在，否则直接进入回退逻辑
            CompanyKnowledgeBase.objects.filter(company=user_company, status='completed').latest('updated_at')
            
            graphrag_dir = os.path.join(settings.BASE_DIR, 'graphrag-main')
            build_view = KnowledgeBaseBuildView()
            config_data = build_view._create_company_config(str(user_company.id), graphrag_dir)
            config_file_path = os.path.join(graphrag_dir, 'ragtest', f'config_company_{user_company.id}.yml')
            with open(config_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, allow_unicode=True, sort_keys=False)

            cmd_args = ["python", "-u", "-m", "graphrag", "query", "--method", method, "--config", os.path.relpath(config_file_path, graphrag_dir), "--query", query_text, "--streaming"]
            env = build_view._get_subprocess_env()
            
            # 记录执行命令
            cmd_str = " ".join(cmd_args)
            graphrag_logger.info(f"执行GraphRAG查询命令: {cmd_str}")
            graphrag_logger.info(f"查询文本: {query_text}")
            graphrag_logger.info(f"查询方法: {method}")
            graphrag_logger.info(f"配置文件: {os.path.relpath(config_file_path, graphrag_dir)}")

            # 移除text=True参数，使用bytes模式
            process = subprocess.Popen(cmd_args, cwd=graphrag_dir, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            def stream_response():
                reader = io.TextIOWrapper(process.stdout, encoding='utf-8', errors='replace')
                assistant_response = ""  # 用于收集完整的AI响应

                in_json_log_block = False
                brace_level = 0
                
                # 创建一个变量保存stderr输出
                stderr_data = []
                
                # 启动一个线程读取stderr并实时输出到控制台
                def log_stderr():
                    try:
                        stderr_reader = io.TextIOWrapper(process.stderr, encoding='utf-8', errors='replace')
                        for line in iter(stderr_reader.readline, ''):
                            if line.strip():
                                stderr_data.append(line)  # 保存stderr输出
                                graphrag_logger.debug(f"GraphRAG stderr: {line.strip()}")
                    except Exception as e:
                        graphrag_logger.error(f"stderr读取线程出错: {e}")
                
                stderr_thread = threading.Thread(target=log_stderr)
                stderr_thread.daemon = True
                stderr_thread.start()
                
                try:
                    for line in iter(reader.readline, ''):
                        # 打印GraphRAG输出到控制台
                        if line.strip():
                            graphrag_logger.debug(f"GraphRAG stdout: {line.strip()}")
                        
                        # 过滤掉包含"Vector Store Args"的JSON日志块
                        if in_json_log_block:
                            brace_level += line.count('{')
                            brace_level -= line.count('}')
                            if brace_level <= 0:
                                in_json_log_block = False
                            continue
                        
                        if "INFO: Vector Store Args" in line:
                            in_json_log_block = True
                            brace_level = line.count('{') - line.count('}')
                            if brace_level <= 0:
                                in_json_log_block = False
                            continue

                        # 过滤掉 [Data: Sources (X)] 标记
                        cleaned_line = re.sub(r'\[Data: Sources \(\d+\)\]\.?', '', line)
                        
                        if cleaned_line.strip():
                            assistant_response += cleaned_line
                            yield f"data: {json.dumps({'type': 'text_chunk', 'content': cleaned_line})}\n\n"
                except Exception as e:
                    graphrag_logger.error(f"读取stdout时出错: {e}", exc_info=True)
                    yield f"data: {json.dumps({'type': 'error', 'content': f'读取过程中出错: {str(e)}'})}\n\n"

                # 关闭读取器和进程输出流
                try:
                    process.stdout.close()
                except:
                    pass
                
                # 等待进程结束
                return_code = process.wait()
                graphrag_logger.info(f"GraphRAG查询进程已结束，返回码: {return_code}")
                
                # 确保stderr线程有时间完成
                stderr_thread.join(timeout=2)
                
                if return_code != 0:
                    # 使用已经收集的stderr数据而不是尝试读取可能已关闭的stderr流
                    error_text = "".join(stderr_data)
                    if not error_text:
                        error_text = "未能获取错误详情，但命令执行失败"
                    
                    graphrag_logger.error(f"GraphRAG查询失败。返回码: {return_code}，错误信息: {error_text}")
                    error_payload = {"type": "error", "content": f"知识库查询失败: {error_text[:200]}"}
                    assistant_response = f"知识库查询失败: {error_text[:200]}"
                    yield f"data: {json.dumps(error_payload)}\n\n"
                else:
                    graphrag_logger.info("GraphRAG查询成功完成")

                # 保存AI的响应到数据库
                if assistant_response:
                    AIChatMessage.objects.create(
                        chat=chat,
                        role='assistant',
                        content=assistant_response,
                        source='knowledge_base'
                    )
                
                # 返回聊天会话ID
                yield f"data: {json.dumps({'type': 'session_id', 'chat_id': str(chat.id)})}\n\n"
            
            return StreamingHttpResponse(stream_response(), content_type='text/event-stream')

        except CompanyKnowledgeBase.DoesNotExist:
            def fallback_stream():
                try:
                    graphrag_logger.warning(f"知识库不存在，为公司 {user_company.id} 回退到通用AI。")
                    ai_assistant = LangChainAssistant(user=request.user)
                    initial_message = {"type": "text_chunk", "content": "知识库尚未构建或未构建成功，本次回答由通用大模型提供。\n\n"}
                    yield f"data: {json.dumps(initial_message)}\n\n"
                    messages = [{'role': 'user', 'content': query_text}]
                    
                    assistant_response = "知识库尚未构建或未构建成功，本次回答由通用大模型提供。\n\n"
                    
                    for chunk in ai_assistant.chat_with_tools_stream(messages):
                        try:
                            # 尝试解析JSON
                            data = json.loads(chunk)
                            if data.get("content"):
                                assistant_response += data.get("content", "")
                        except json.JSONDecodeError:
                            # 如果不是JSON，直接累加
                            assistant_response += chunk
                        
                        yield f"data: {chunk}\n\n"
                    
                    # 保存AI的响应到数据库
                    if assistant_response:
                        AIChatMessage.objects.create(
                            chat=chat,
                            role='assistant',
                            content=assistant_response,
                            source='general_ai'
                        )
                    
                    # 返回聊天会话ID
                    yield f"data: {json.dumps({'type': 'session_id', 'chat_id': str(chat.id)})}\n\n"
                except Exception as e:
                    graphrag_logger.error(f"通用AI模型回退失败: {e}")
                    error_payload = {"type": "error", "content": "知识库和备用AI模型均调用失败。"}
                    yield f"data: {json.dumps(error_payload)}\n\n"
            return StreamingHttpResponse(fallback_stream(), content_type='text/event-stream')
        except Exception as e:
            graphrag_logger.error(f"GraphRAG查询准备阶段出错: {e}", exc_info=True)
            # 对于准备阶段的错误，可以直接返回错误响应
            return Response({'status': 'error', 'message': f'查询时发生内部错误: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KnowledgeGraphDataView(APIView):
    """知识图谱数据API视图"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """获取知识图谱数据"""
        try:
            user_company = request.user.company
            if not user_company:
                return Response({'error': '用户未关联任何公司'}, status=status.HTTP_400_BAD_REQUEST)

            # 检查知识库是否存在
            try:
                knowledge_base = CompanyKnowledgeBase.objects.filter(
                    company=user_company, 
                    status='completed'
                ).latest('updated_at')
            except CompanyKnowledgeBase.DoesNotExist:
                return Response({
                    'nodes': [],
                    'edges': [],
                    'categories': [],
                    'message': '知识库尚未构建完成'
                }, status=status.HTTP_200_OK)

            # GraphRAG输出目录
            graphrag_output_dir = os.path.join(
                settings.BASE_DIR, 'graphrag-main', 'ragtest', 'output'
            )
            
            # 查找最新的输出目录
            latest_output_dir = self._find_latest_output_dir(graphrag_output_dir)
            if not latest_output_dir:
                return Response({
                    'nodes': [],
                    'edges': [],
                    'categories': [],
                    'message': '未找到GraphRAG输出数据'
                }, status=status.HTTP_200_OK)

            # 读取实体和关系数据
            entities_data = self._load_entities_data(latest_output_dir)
            relationships_data = self._load_relationships_data(latest_output_dir)
            
            # 处理数据并返回
            graph_data = self._process_graph_data(entities_data, relationships_data, request)
            
            return Response(graph_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"获取知识图谱数据失败: {e}", exc_info=True)
            return Response({
                'error': f'获取知识图谱数据失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _find_latest_output_dir(self, base_output_dir):
        """查找最新的输出目录"""
        try:
            if not os.path.exists(base_output_dir):
                return None
            
            # 查找所有company_*目录
            company_dirs = []
            for item in os.listdir(base_output_dir):
                item_path = os.path.join(base_output_dir, item)
                if os.path.isdir(item_path) and item.startswith('company_'):
                    company_dirs.append(item_path)
            
            if not company_dirs:
                # 如果没有company_*目录，尝试查找时间戳目录作为备选
                timestamp_dirs = []
                for item in os.listdir(base_output_dir):
                    item_path = os.path.join(base_output_dir, item)
                    if os.path.isdir(item_path) and item.replace('-', '').replace('T', '').replace(':', '').isdigit():
                        timestamp_dirs.append(item_path)
                return max(timestamp_dirs, key=os.path.getmtime) if timestamp_dirs else None
                
            # 返回最新的company目录
            return max(company_dirs, key=os.path.getmtime)
            
        except Exception as e:
            logger.error(f"查找输出目录失败: {e}")
            return None

    def _load_entities_data(self, output_dir):
        """加载实体数据"""
        try:
            entities_file = os.path.join(output_dir, 'entities.parquet')
            if not os.path.exists(entities_file):
                logger.warning(f"实体文件不存在: {entities_file}")
                return []
            
            df = pd.read_parquet(entities_file)
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"加载实体数据失败: {e}")
            return []

    def _load_relationships_data(self, output_dir):
        """加载关系数据"""
        try:
            relationships_file = os.path.join(output_dir, 'relationships.parquet')
            if not os.path.exists(relationships_file):
                logger.warning(f"关系文件不存在: {relationships_file}")
                return []
            
            df = pd.read_parquet(relationships_file)
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"加载关系数据失败: {e}")
            return []

    def _safe_float(self, value, default=0.0):
        """安全处理浮点数，确保JSON兼容"""
        if value is None:
            return default
        try:
            float_val = float(value)
            if math.isfinite(float_val):
                return float_val
            else:
                return default
        except (ValueError, TypeError):
            return default
    
    def _process_graph_data(self, entities_data, relationships_data, request):
        """处理图谱数据"""
        try:
            # 获取参数
            node_limit = int(request.GET.get('node_limit', 100))
            edge_limit = int(request.GET.get('edge_limit', 200))
            
            # 处理实体数据
            nodes = []
            entity_types = set()
            
            for i, entity in enumerate(entities_data[:node_limit]):
                entity_type = entity.get('type', 'UNKNOWN')
                entity_types.add(entity_type)
                
                node = {
                    'id': entity.get('human_readable_id', entity.get('id', f'entity_{i}')),
                    'name': entity.get('title', f'Entity {i}'),
                    'type': entity_type,
                    'description': entity.get('description', ''),
                    'category': entity_type,
                    'symbolSize': min(max(self._safe_float(entity.get('degree'), 10), 10), 50),  # 节点大小基于度数
                    'x': self._safe_float(entity.get('x')),
                    'y': self._safe_float(entity.get('y')),
                    'value': self._safe_float(entity.get('degree'), 1)
                }
                nodes.append(node)
            
            # 处理关系数据
            edges = []
            # 创建从实体名称到human_readable_id的映射
            entity_name_to_id = {node['name']: node['id'] for node in nodes}
            
            for i, rel in enumerate(relationships_data[:edge_limit]):
                source_name = rel.get('source')
                target_name = rel.get('target')
                
                # 只包含存在于节点中的关系
                if source_name in entity_name_to_id and target_name in entity_name_to_id:
                    edge = {
                        'id': f'edge_{i}',
                        'source': entity_name_to_id[source_name],
                        'target': entity_name_to_id[target_name],
                        'relation': rel.get('description', '关联'),
                        'weight': self._safe_float(rel.get('weight'), 1),
                        'value': self._safe_float(rel.get('weight'), 1)
                    }
                    edges.append(edge)
            
            # 生成类别配置
            categories = []
            colors = [
                '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
                '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#ff9f7f'
            ]
            
            for i, entity_type in enumerate(sorted(entity_types)):
                categories.append({
                    'name': entity_type,
                    'color': colors[i % len(colors)]
                })
            
            return {
                'nodes': nodes,
                'edges': edges,
                'categories': categories,
                'stats': {
                    'total_nodes': len(nodes),
                    'total_edges': len(edges),
                    'entity_types': len(entity_types)
                }
            }
            
        except Exception as e:
            logger.error(f"处理图谱数据失败: {e}")
            return {
                'nodes': [],
                'edges': [],
                'categories': [],
                'error': str(e)
            }


class KnowledgeEntityDetailView(APIView):
    """实体详情API视图"""
    permission_classes = [IsAuthenticated]

    def get(self, request, entity_id):
        """获取实体详情和关联关系"""
        try:
            logger.info(f"DEBUG KnowledgeEntityDetailView: 请求实体详情，entity_id='{entity_id}'，类型={type(entity_id)}")
            
            user_company = request.user.company
            if not user_company:
                logger.warning(f"ERROR 用户未关联任何公司")
                return Response({'error': '用户未关联任何公司'}, status=status.HTTP_400_BAD_REQUEST)

            # GraphRAG输出目录
            graphrag_output_dir = os.path.join(
                settings.BASE_DIR, 'graphrag-main', 'ragtest', 'output'
            )
            logger.info(f"DIR GraphRAG输出目录: {graphrag_output_dir}")
            
            # 查找最新的输出目录
            graph_data_view = KnowledgeGraphDataView()
            latest_output_dir = graph_data_view._find_latest_output_dir(graphrag_output_dir)
            logger.info(f"FOLDER 最新输出目录: {latest_output_dir}")
            
            if not latest_output_dir:
                logger.error(f"ERROR 未找到GraphRAG输出数据")
                return Response({'error': '未找到GraphRAG输出数据'}, status=status.HTTP_404_NOT_FOUND)

            # 加载数据
            entities_data = graph_data_view._load_entities_data(latest_output_dir)
            relationships_data = graph_data_view._load_relationships_data(latest_output_dir)
            logger.info(f"DATA 加载数据完成: 实体数量={len(entities_data)}, 关系数量={len(relationships_data)}")
            
            # 调试：显示前几个实体的ID信息
            if entities_data:
                logger.info(f"DEBUG 前5个实体的ID信息:")
                for i, e in enumerate(entities_data[:5]):
                    logger.info(f"  实体{i+1}: human_readable_id='{e.get('human_readable_id')}', id='{e.get('id')}', title='{e.get('title')}'")
            
            # 查找指定实体
            entity = None
            logger.info(f"DEBUG 开始查找实体，目标entity_id='{entity_id}'")
            
            # 检查是否是前端生成的node_X格式ID
            if entity_id.startswith('node_'):
                try:
                    # 提取索引号
                    node_index = int(entity_id.split('_')[1])
                    logger.info(f"DEBUG 检测到前端生成的节点ID格式，索引={node_index}")
                    
                    # 根据索引直接获取实体（需要考虑node_limit限制）
                    node_limit = int(request.GET.get('node_limit', 100))
                    if 0 <= node_index < min(len(entities_data), node_limit):
                        entity = entities_data[node_index]
                        logger.info(f"SUCCESS 通过索引找到实体: 索引={node_index}, title='{entity.get('title')}'")
                    else:
                        logger.warning(f"WARNING 节点索引超出范围: {node_index}, 最大索引={min(len(entities_data), node_limit)-1}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"WARNING 解析前端节点ID失败: {e}")
            
            # 如果通过前端ID格式没找到，尝试其他匹配方式
            if not entity:
                for i, e in enumerate(entities_data):
                    human_readable_id = e.get('human_readable_id')
                    entity_id_field = e.get('id')
                    title = e.get('title')
                    
                    # 尝试多种匹配方式
                    if (human_readable_id == entity_id or 
                        entity_id_field == entity_id or 
                        title == entity_id or
                        str(human_readable_id) == str(entity_id) or
                        str(entity_id_field) == str(entity_id) or
                        str(title) == str(entity_id)):
                        entity = e
                        logger.info(f"SUCCESS 找到匹配实体: 索引={i}, human_readable_id='{human_readable_id}', id='{entity_id_field}', title='{title}'")
                        break
            
            if not entity:
                logger.error(f"ERROR 实体不存在，entity_id='{entity_id}'")
                logger.error(f"LIST 可用的实体ID列表:")
                for i, e in enumerate(entities_data[:10]):
                    logger.error(f"  {i+1}. human_readable_id='{e.get('human_readable_id')}', id='{e.get('id')}', title='{e.get('title')}'")
                return Response({'error': '实体不存在'}, status=status.HTTP_404_NOT_FOUND)
            
            # 查找相关关系
            relationships = []
            # 获取当前实体的所有可能标识符
            entity_identifiers = {
                entity.get('human_readable_id'),
                entity.get('id'),
                entity.get('title'),
                str(entity.get('human_readable_id')),
                str(entity.get('id')),
                str(entity.get('title'))
            }
            # 移除None值
            entity_identifiers = {id for id in entity_identifiers if id is not None}
            
            logger.info(f"DEBUG 实体标识符集合: {entity_identifiers}")
            logger.info(f"DATA 开始查找关系，总关系数量: {len(relationships_data)}")
            
            for i, rel in enumerate(relationships_data):
                source = rel.get('source')
                target = rel.get('target')
                
                # 检查是否为出向关系（当前实体作为源）
                if source in entity_identifiers:
                    logger.info(f"SUCCESS 找到出向关系 {i+1}: {source} -> {target}")
                    relationships.append({
                        'id': rel.get('id'),
                        'targetId': target,
                        'targetName': self._get_entity_name(target, entities_data),
                        'relation': rel.get('description', '关联'),
                        'weight': graph_data_view._safe_float(rel.get('weight'), 1),
                        'direction': 'outgoing'
                    })
                # 检查是否为入向关系（当前实体作为目标）
                elif target in entity_identifiers:
                    logger.info(f"SUCCESS 找到入向关系 {i+1}: {source} -> {target}")
                    relationships.append({
                        'id': rel.get('id'),
                        'sourceId': source,
                        'sourceName': self._get_entity_name(source, entities_data),
                        'relation': rel.get('description', '关联'),
                        'weight': graph_data_view._safe_float(rel.get('weight'), 1),
                        'direction': 'incoming'
                    })
            
            logger.info(f"RESULT 关系查找完成，找到 {len(relationships)} 个关系")
            
            return Response({
                'entity': {
                    'id': entity.get('human_readable_id', entity.get('id')),
                    'name': entity.get('title'),
                    'type': entity.get('type'),
                    'description': entity.get('description'),
                    'degree': graph_data_view._safe_float(entity.get('degree')),
                    'x': graph_data_view._safe_float(entity.get('x')),
                    'y': graph_data_view._safe_float(entity.get('y'))
                },
                'relationships': relationships
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"获取实体详情失败: {e}", exc_info=True)
            return Response({
                'error': f'获取实体详情失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_entity_name(self, entity_id, entities_data):
        """根据实体ID获取实体名称"""
        for entity in entities_data:
            # 检查多种可能的匹配方式
            if (entity.get('human_readable_id') == entity_id or 
                entity.get('id') == entity_id or
                entity.get('title') == entity_id or
                str(entity.get('human_readable_id')) == str(entity_id) or
                str(entity.get('id')) == str(entity_id) or
                str(entity.get('title')) == str(entity_id)):
                return entity.get('title', entity_id)
        return entity_id
