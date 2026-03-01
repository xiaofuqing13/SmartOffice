from rest_framework import viewsets, permissions
from .models import Project, ProjectMember, Task, Company, ProjectDocument, TaskCompletion, Requirement
from .serializers import ProjectSerializer, ProjectMemberSerializer, TaskSerializer, CompanySerializer, ProjectDocumentSerializer, TaskCompletionSerializer, RequirementSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from apps.users.serializers import UserSimpleSerializer
import logging
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import mixins
from django.db import models
import yaml
import os
from langchain_community.llms import OpenAI
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import ChatPromptTemplate
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import FileResponse
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import base64, re
from reportlab.lib import colors
from rest_framework.pagination import PageNumberPagination
from reportlab.lib.colors import HexColor
import traceback
from rest_framework.renderers import JSONRenderer
from .renderers import PDFRenderer

User = get_user_model()
logger = logging.getLogger(__name__)

# AI配置和工具类
class AIService:
    """AI服务类，提供项目各模块的AI分析能力"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.api_key = None
        self.api_base = None
        self.model = None
        self.llm = None
        self._load_config()
        self._initialize_llm()
        self._initialized = True
    
    def _load_config(self):
        """从配置文件加载AI设置"""
        try:
            # 彻底修正配置文件路径，连退三级，确保指向 smart-office/backend/setting.yaml
            settings_path = os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(os.path.abspath(__file__))
                    )
                ),
                'setting.yaml'
            )
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = yaml.safe_load(f)
                    ai_settings = settings.get('ai', {})
                    self.api_key = ai_settings.get('openai_api_key', '')
                    self.api_base = ai_settings.get('openai_api_base', '')
                    self.model = ai_settings.get('model', 'gpt-3.5-turbo')
                    logger.info(f"成功加载AI配置: model={self.model}")
            else:
                logger.warning(f"AI配置文件不存在: {settings_path}")
        except Exception as e:
            logger.error(f"加载AI配置失败: {e}")
    
    def _initialize_llm(self):
        """初始化语言模型"""
        try:
            if not self.api_key:
                logger.warning("API密钥未配置，无法初始化LLM")
                return
                
            # 设置环境变量
            os.environ["OPENAI_API_KEY"] = self.api_key
            if self.api_base:
                os.environ["OPENAI_API_BASE"] = self.api_base
            
            self.llm = ChatOpenAI(
                model=self.model,
                temperature=0.7,
                max_tokens=1024
            )
            logger.info(f"LLM初始化成功: {self.model}")
        except Exception as e:
            logger.error(f"初始化LLM失败: {e}")
            self.llm = None
    
    def is_available(self):
        """检查AI服务是否可用"""
        return self.llm is not None
    
    def analyze_task(self, task):
        """分析任务并提供建议"""
        if not self.is_available():
            return ["AI分析服务不可用"]
        try:
            llm = self.llm
            prompt = f"""
            请对以下项目任务进行分析，并提供3-5条有价值的建议:
            任务名称: {task.title}
            任务描述: {task.description or '无描述'}
            优先级: {task.priority}
            状态: {task.status}
            截止日期: {task.due_date or '未设置'}
            请从任务紧急性、重要性、可行性等角度提供专业分析和建议:
            """
            from langchain.prompts import PromptTemplate
            prompt_template = PromptTemplate(input_variables=['input'], template="{input}")
            chain = prompt_template | llm
            result = chain.invoke({"input": prompt})
            result_text = result.content if hasattr(result, 'content') else str(result)
            suggestions = [s.strip() for s in result_text.split('\n') if s.strip()]
            return suggestions[:5]
        except Exception as e:
            logger.error(f"任务AI分析失败: {e}", exc_info=True)
            return ["AI分析过程中出现错误"]
    
    def analyze_document(self, document):
        """分析文档并提供摘要和关键信息提取"""
        if not self.is_available():
            return "AI分析服务不可用"
        try:
            llm = self.llm
            prompt = f"""
            请对以下项目文档进行分析:
            文档名称: {document.name}
            文档描述: {document.desc or '无描述'}
            标签: {document.tags or '无标签'}
            请提供简短的文档分析，包括该文档可能的用途、与项目的关系以及对项目的重要性:
            """
            from langchain.prompts import PromptTemplate
            prompt_template = PromptTemplate(input_variables=['input'], template="{input}")
            chain = prompt_template | llm
            result = chain.invoke({"input": prompt})
            result_text = result.content if hasattr(result, 'content') else str(result)
            return result_text
        except Exception as e:
            logger.error(f"文档AI分析失败: {e}", exc_info=True)
            return "AI分析过程中出现错误"
    
    def analyze_project(self, project, tasks=None, documents=None, requirements=None):
        """项目整体分析，包括健康度评估和风险预警"""
        if not self.is_available():
            return {
                "health": 0,
                "health_desc": "AI分析服务不可用",
                "risks": []
            }
        
        try:
            task_count = len(tasks) if tasks else 0
            doc_count = len(documents) if documents else 0
            req_count = len(requirements) if requirements else 0
            todo_tasks = len([t for t in tasks if t.status == 'todo']) if tasks else 0
            in_progress_tasks = len([t for t in tasks if t.status == 'in-progress']) if tasks else 0
            done_tasks = len([t for t in tasks if t.status == 'done']) if tasks else 0
            import datetime
            today = datetime.date.today()
            overdue_tasks = [t for t in tasks if t.due_date and t.due_date < today and t.status != 'done'] if tasks else []
            llm = self.llm
            prompt = f"""
            请分析以下项目数据，评估项目健康度(0-100)并提供健康状况描述和风险预警:
            项目名称: {getattr(project, 'name', '') or '未命名'}
            项目描述: {getattr(project, 'desc', '') or '无描述'}
            开始日期: {str(getattr(project, 'start', '') or '未设置')}
            结束日期: {str(getattr(project, 'end', '') or '未设置')}
            当前状态: {getattr(project, 'status', '') or '未知'}
            任务总数: {task_count}
            - 待处理任务: {todo_tasks}
            - 进行中任务: {in_progress_tasks}
            - 已完成任务: {done_tasks}
            - 逾期任务数: {len(overdue_tasks)}
            文档数量: {doc_count}
            需求数量: {req_count}
            请提供:
            1. 项目健康度评分(0-100的整数)
            2. 项目健康状况简短描述(一句话)
            3. 列出2-3个项目风险点
            按照以下格式返回:
            健康度评分: 分数
            健康状况: 描述
            风险点1: xxx
            风险点2: xxx
            """
            from langchain.prompts import PromptTemplate
            prompt_template = PromptTemplate(input_variables=['input'], template="{input}")
            chain = prompt_template | llm
            result = chain.invoke({"input": prompt})
            result_text = result.content if hasattr(result, 'content') else str(result)
            lines = result_text.strip().split('\n')
            health_score = 0
            health_desc = ""
            risks = []
            for line in lines:
                if line.startswith("健康度评分:"):
                    try:
                        health_score = int(line.split(":", 1)[1].strip())
                    except:
                        health_score = 50
                elif line.startswith("健康状况:"):
                    health_desc = line.split(":", 1)[1].strip()
                elif line.startswith("风险点"):
                    risk = line.split(":", 1)[1].strip() if ":" in line else line
                    risks.append(risk)
            return {
                "health": health_score,
                "health_desc": health_desc,
                "risks": risks
            }
        except Exception as e:
            logger.error(f"项目AI分析失败: {e}", exc_info=True)
            return {
                "health": 50,
                "health_desc": "项目分析出现错误",
                "risks": ["无法完成风险评估"]
            }

    def analyze_requirement(self, requirements):
        if not self.is_available():
            return {
                "completeness": 0,
                "dependencies": 0,
                "conflicts": 0,
                "suggestions": ["AI分析服务不可用"]
            }
        try:
            # 兼容处理字典和对象
            req_info = "\n".join([
                f"需求{i+1}. {r.get('name', '') if isinstance(r, dict) else r.name}: {r.get('description', '无描述') if isinstance(r, dict) else r.description or '无描述'} [优先级:{r.get('priority', '') if isinstance(r, dict) else r.priority}]" 
                for i, r in enumerate(requirements[:10])
            ])
            llm = self.llm
            prompt = f"""
            请分析以下项目需求列表，并提供以下指标:
            {req_info}
            请提供:
            1. 需求完整性评分(0-100的整数)
            2. 可能存在的需求依赖关系数量
            3. 可能的需求冲突数量
            4. 2-3条关于需求的建议
            按照以下格式返回:
            完整性评分: 分数
            依赖关系: 数量
            需求冲突: 数量
            建议1: xxx
            建议2: xxx
            """
            from langchain.prompts import PromptTemplate
            prompt_template = PromptTemplate(input_variables=['input'], template="{input}")
            chain = prompt_template | llm
            result = chain.invoke({"input": prompt})
            result_text = result.content if hasattr(result, 'content') else str(result)
            lines = result_text.strip().split('\n')
            completeness = 0
            dependencies = 0
            conflicts = 0
            suggestions = []
            for line in lines:
                if line.startswith("完整性评分:"):
                    try:
                        completeness = int(line.split(":", 1)[1].strip())
                    except:
                        completeness = 70
                elif line.startswith("依赖关系:"):
                    try:
                        dependencies = int(line.split(":", 1)[1].strip())
                    except:
                        dependencies = 5
                elif line.startswith("需求冲突:"):
                    try:
                        conflicts = int(line.split(":", 1)[1].strip())
                    except:
                        conflicts = 2
                elif line.startswith("建议"):
                    suggestion = line.split(":", 1)[1].strip() if ":" in line else line
                    suggestions.append(suggestion)
            if not suggestions:
                suggestions = ["建议优化需求描述，增加细节", "考虑按功能对需求进行分类"]
            return {
                "completeness": completeness,
                "dependencies": dependencies,
                "conflicts": conflicts,
                "suggestions": suggestions
            }
        except Exception as e:
            logger.error(f"需求AI分析失败: {e}", exc_info=True)
            return {
                "completeness": 70,
                "dependencies": len(requirements) // 2,
                "conflicts": min(2, len(requirements) // 5),
                "suggestions": ["AI分析过程中出现错误，这是估算数据", "建议完善需求描述"]
            }

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        company = self.get_object()
        users = User.objects.filter(company=company)
        logger.info(f"CompanyViewSet.users: 查询公司ID={pk}的用户，找到{users.count()}个用户")
        return Response(UserSimpleSerializer(users, many=True).data)

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    # 添加分页设置
    class ProjectPagination(PageNumberPagination):
        page_size = 10  # 默认每页显示10条
        page_size_query_param = 'page_size'  # 允许客户端通过page_size参数覆盖默认值
        max_page_size = 100  # 最大每页显示数量
    
    pagination_class = ProjectPagination

    def get_queryset(self):
        user = self.request.user
        # 如果用户有公司信息，只显示该公司的项目
        if user.company:
            return Project.objects.filter(company=user.company).order_by('-id')
        return Project.objects.none()

    def perform_create(self, serializer):
        """创建项目时自动设置创建者的公司作为项目的公司"""
        if self.request.user.company:
            serializer.save(company=self.request.user.company)
        else:
            raise serializers.ValidationError("用户未关联公司，无法创建项目")

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """获取项目成员列表"""
        project = self.get_object()
        members = ProjectMember.objects.filter(project=project)
        serializer = ProjectMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def ai_dashboard(self, request, pk=None):
        """项目AI仪表盘分析接口"""
        project = self.get_object()
        ai_service = AIService()
        
        if not ai_service.is_available():
            return Response({
                "health": 70,
                "health_desc": "AI服务不可用，显示默认数据",
                "risks": [
                    {"title": "进度风险", "description": "请检查项目进度"},
                    {"title": "质量风险", "description": "建议进行代码审查"}
                ],
                "ai_suggestions": [
                    {"title": "完善文档", "desc": "项目文档需要更新", "type": "document"},
                    {"title": "任务分配", "desc": "考虑重新分配任务", "type": "task"}
                ]
            })
            
        # 获取项目相关数据
        tasks = Task.objects.filter(project=project)
        documents = ProjectDocument.objects.filter(project=project)
        requirements = Requirement.objects.filter(project=project)
        
        # 进行项目整体分析
        try:
            analysis = ai_service.analyze_project(project, tasks, documents, requirements)
            return Response(analysis)
        except Exception as e:
            logger.error(f"项目AI分析失败: {str(e)}")
            # 返回默认数据
            return Response({
                "health": 65,
                "health_desc": "项目健康度一般，需要关注进度和质量",
                "risks": [
                    {"title": "分析失败", "description": f"AI分析出错: {str(e)}"}
                ],
                "ai_suggestions": [
                    {"title": "重试分析", "desc": "请稍后重试AI分析", "type": "system"}
                ]
            })

    @action(detail=True, methods=['post'], renderer_classes=[PDFRenderer, JSONRenderer])
    def export_ai_report(self, request, pk=None):
        """导出项目AI分析报告为PDF（含图表，规范排版）"""
        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from django.http import FileResponse
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.utils import ImageReader
        from reportlab.lib.colors import HexColor
        import base64, re, textwrap, os, traceback
        
        # 注册中文字体 - 增强字体处理逻辑
        DEFAULT_FONT = 'Helvetica'  # 默认英文字体
        try:
            # 检查多个常见字体位置
            font_paths = [
                'C:/Windows/Fonts/simsun.ttc',  # Windows 宋体
                'C:/Windows/Fonts/simhei.ttf',  # Windows 黑体
                'C:/Windows/Fonts/msyh.ttc',    # Windows 微软雅黑
                'C:/Windows/Fonts/msyhbd.ttc',  # Windows 微软雅黑粗体
                '/usr/share/fonts/chinese/simsun.ttc',  # Linux
                '/usr/share/fonts/truetype/arphic/uming.ttc',  # Linux
            ]
            
            font_loaded = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        if font_path.endswith('simsun.ttc'):
                            pdfmetrics.registerFont(TTFont('SimSun', font_path))
                            DEFAULT_FONT = 'SimSun'
                            font_loaded = True
                            logger.info(f"成功加载字体: SimSun from {font_path}")
                            break
                        elif font_path.endswith('simhei.ttf'):
                            pdfmetrics.registerFont(TTFont('SimHei', font_path))
                            DEFAULT_FONT = 'SimHei'
                            font_loaded = True
                            logger.info(f"成功加载字体: SimHei from {font_path}")
                            break
                        elif font_path.endswith('msyh.ttc'):
                            pdfmetrics.registerFont(TTFont('MSYaHei', font_path))
                            DEFAULT_FONT = 'MSYaHei'
                            font_loaded = True
                            logger.info(f"成功加载字体: MSYaHei from {font_path}")
                            break
                        elif font_path.endswith('msyhbd.ttc'):
                            pdfmetrics.registerFont(TTFont('MSYaHeiBold', font_path))
                            DEFAULT_FONT = 'MSYaHeiBold'
                            font_loaded = True
                            logger.info(f"成功加载字体: MSYaHeiBold from {font_path}")
                            break
                        elif font_path.endswith('uming.ttc'):
                            pdfmetrics.registerFont(TTFont('UMing', font_path))
                            DEFAULT_FONT = 'UMing'
                            font_loaded = True
                            logger.info(f"成功加载字体: UMing from {font_path}")
                            break
                    except Exception as font_error:
                        logger.error(f"加载字体 {font_path} 失败: {font_error}")
                        continue
            
            if not font_loaded:
                logger.warning("未找到中文字体，将使用Helvetica，中文可能无法正确显示")
        except Exception as e:
            logger.error(f"加载字体失败: {e}")
            logger.error(traceback.format_exc())
        
        project = self.get_object()
        ai_service = AIService()
        if not ai_service.is_available():
            return Response({"error": "AI服务不可用，无法导出报告"}, status=500)
        
        # 获取项目相关数据
        tasks = Task.objects.filter(project=project)
        documents = ProjectDocument.objects.filter(project=project)
        requirements = Requirement.objects.filter(project=project)
        
        # 获取AI分析结果
        project_analysis = ai_service.analyze_project(project, tasks, documents, requirements)
        req_analysis = ai_service.analyze_requirement(requirements)
        
        # 获取图表分析数据
        try:
            chart_analysis = self.chart_analysis(request, pk=pk).data
        except Exception as e:
            logger.error(f"获取图表分析失败: {e}")
            chart_analysis = {}
        
        # 解析前端传来的图片 - 增强错误处理
        def b64img2bytes(b64str):
            if not b64str:
                logger.warning("接收到空的图表数据")
                return None
            try:
                # 移除可能的 data:image 前缀
                if isinstance(b64str, str):
                    if ',' in b64str:
                        b64str = b64str.split(',', 1)[1]
                    else:
                        b64str = re.sub('^data:image/\w+;base64,', '', b64str)
                    
                    # 尝试解码
                    img_data = base64.b64decode(b64str)
                    # 验证数据有效性（简单检查文件头）
                    if len(img_data) < 10:
                        logger.warning(f"Base64解码后数据太小: {len(img_data)}字节")
                        return None
                        
                    logger.info(f"成功解析Base64图像数据: {len(img_data)}字节")
                    return img_data
                else:
                    logger.warning(f"接收到非字符串类型的图表数据: {type(b64str)}")
                    return None
            except Exception as e:
                logger.error(f"Base64解码失败: {e}")
                return None
        
        # 记录请求中的数据类型
        logger.info(f"接收到图表数据: doc_trend_img类型={type(request.data.get('doc_trend_img'))}, "
                   f"req_chart_img类型={type(request.data.get('req_chart_img'))}")
        
        # 尝试解析图表数据
        try:
            doc_trend_img = b64img2bytes(request.data.get('doc_trend_img'))
            req_chart_img = b64img2bytes(request.data.get('req_chart_img'))
            gauge_chart_img = b64img2bytes(request.data.get('gauge_chart_img'))
            trend_chart_img = b64img2bytes(request.data.get('trend_chart_img'))
            
            # 记录图像解析结果
            logger.info(f"图表解析结果: doc_trend_img={None if doc_trend_img is None else len(doc_trend_img)}字节, "
                       f"req_chart_img={None if req_chart_img is None else len(req_chart_img)}字节, "
                       f"gauge_chart_img={None if gauge_chart_img is None else len(gauge_chart_img)}字节, "
                       f"trend_chart_img={None if trend_chart_img is None else len(trend_chart_img)}字节")
        except Exception as e:
            logger.error(f"解析图表数据失败: {e}")
            doc_trend_img = req_chart_img = gauge_chart_img = trend_chart_img = None
        
        # 解析导出选项
        export_options = request.data.get('export_options', [])
        if not isinstance(export_options, list):
            export_options = []
        
        # 如果没有指定导出选项，则默认导出所有内容
        if not export_options:
            export_options = ['project_info', 'tasks', 'documents', 'requirements', 'ai_insights']
        
        # 定义页面边距和可打印宽度
        LEFT_MARGIN = 50
        RIGHT_MARGIN = 50
        PAGE_WIDTH, PAGE_HEIGHT = A4
        PRINTABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
        
        # 创建PDF工具函数
        def draw_text_block(p, text, x, y, width=450, font=DEFAULT_FONT, size=12, spacing=16):
            """绘制自动换行的文本块，支持中英文混排（优化版）"""
            if not text: return y
            p.setFont(font, size)
            
            lines = []
            for paragraph in text.split('\n'):
                if not paragraph:
                    lines.append('')
                    continue
                
                current_line = ""
                for char in paragraph:
                    # 使用stringWidth来精确计算行宽
                    if p.stringWidth(current_line + char, font, size) > width:
                        lines.append(current_line)
                        current_line = char
                    else:
                        current_line += char
                
                if current_line:
                    lines.append(current_line)

            for line in lines:
                try:
                    p.drawString(x, y, line)
                except Exception as e:
                    logger.error(f"绘制文本失败: {e}, 内容: {line}")
                    # Fallback for any unexpected character issues
                    safe_line = ''.join(c if ord(c) < 65536 else '?' for c in line)
                    p.drawString(x, y, safe_line)
                y -= spacing
            
            return y
        
        def draw_section_title(p, title, x, y, font=DEFAULT_FONT, size=16, color="#1E88E5"):
            """绘制带有颜色的章节标题"""
            p.setFillColor(HexColor(color))
            p.setFont(font, size)
            p.drawString(x, y, title)
            p.setFillColor(HexColor("#000000"))  # 重置为黑色
            # 绘制下划线
            p.line(x, y-5, x+250, y-5)
            return y - 30  # 返回减去标题高度的y坐标
        
        def draw_subsection_title(p, title, x, y, font=DEFAULT_FONT, size=14, color="#424242"):
            """绘制子标题"""
            p.setFillColor(HexColor(color))
            p.setFont(font, size)
            p.drawString(x, y, title)
            p.setFillColor(HexColor("#000000"))  # 重置为黑色
            return y - 25  # 返回减去标题高度的y坐标
        
        def draw_bullet_list(p, items, x, y, width=450, font=DEFAULT_FONT, size=12, spacing=16, bullet="• "):
            """绘制项目符号列表，支持自动换行（优化版）"""
            if not items: return y
            p.setFont(font, size)
            
            bullet_width = p.stringWidth(bullet, font, size)
            hanging_indent = x + bullet_width
            text_width = width - bullet_width

            for item in items:
                lines = []
                current_line = ""
                # 按字符进行精确换行
                for char in str(item):
                    if p.stringWidth(current_line + char, font, size) > text_width:
                        lines.append(current_line)
                        current_line = char
                    else:
                        current_line += char
                if current_line:
                    lines.append(current_line)
                
                if not lines:
                    continue

                # 绘制第一行（带项目符号）
                p.drawString(x, y, bullet + lines[0])
                y -= spacing

                # 绘制后续行（悬挂缩进）
                for line in lines[1:]:
                    p.drawString(hanging_indent, y, line)
                    y -= spacing
            
            return y
        
        # 检查是否需要创建新页面
        def ensure_space(p, y, needed_space=100, height=A4[1]):
            """确保有足够的空间，否则创建新页面"""
            if y < needed_space:
                p.showPage()
                # 重置文本颜色为黑色
                p.setFillColor(HexColor("#000000"))
                return height - 60  # 页面上方留出一定边距
            return y
        
        # 安全绘制图片的函数
        def safe_draw_image(p, img_data, x, y, w, h):
            """安全地绘制图片，处理异常情况"""
            if img_data is None:
                logger.warning(f"图片数据为空，跳过绘制")
                return False
                
            try:
                img_reader = ImageReader(BytesIO(img_data))
                p.drawImage(img_reader, x, y, width=w, height=h)
                logger.info(f"成功绘制图片: 位置=({x},{y}), 尺寸={w}x{h}")
                return True
            except Exception as e:
                logger.error(f"绘制图片失败: {e}")
                # 绘制一个占位框
                try:
                    p.setFillColor(HexColor("#F5F5F5"))
                    p.rect(x, y, w, h, fill=1, stroke=1)
                    p.setFillColor(HexColor("#999999"))
                    p.setFont(DEFAULT_FONT, 12)
                    p.drawCentredString(x + w/2, y + h/2, "图表加载失败")
                    p.setFillColor(HexColor("#000000"))  # 重置颜色
                except Exception as inner_e:
                    logger.error(f"绘制占位框也失败了: {inner_e}")
                return False
        
        try:
            # 生成PDF
            buffer = BytesIO()
            width, height = A4
            
            p = canvas.Canvas(buffer, pagesize=A4)
            p.setTitle(f"{project.name} - 项目AI分析报告")
            
            # 封面
            p.setFillColor(HexColor("#1E88E5"))
            p.rect(0, 0, width, height, fill=1)
            p.setFillColor(HexColor("#FFFFFF"))
            
            p.setFont(DEFAULT_FONT, 36)
            p.drawCentredString(width/2, height-180, "项目AI分析报告")
            
            p.setFont(DEFAULT_FONT, 24)
            p.drawCentredString(width/2, height-250, f"{project.name}")
            
            p.setFont(DEFAULT_FONT, 16)
            import datetime
            p.drawCentredString(width/2, height-300, f"生成日期：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            # 在封面底部加一条横线和版权信息
            p.line(50, 100, width-50, 100)
            p.setFont(DEFAULT_FONT, 12)
            p.drawCentredString(width/2, 80, "智行舟系统自动生成")
            p.drawCentredString(width/2, 60, "© 智行舟系统")
            
            p.showPage()
            
            # 设置默认文本颜色为黑色
            p.setFillColor(HexColor("#000000"))
            
            # 准备目录项
            toc_items = []
            page_counter = 2  # 从第2页开始计数
            
            # 根据导出选项构建目录
            if 'project_info' in export_options:
                toc_items.append({"title": "1. 项目概况", "page": page_counter})
                page_counter += 1
                
                if 'project_health' in export_options or 'ai_insights' in export_options:
                    toc_items.append({"title": "2. 项目健康评估", "page": page_counter})
                    page_counter += 1
                    
            section_idx = len(toc_items) + 1
            
            if 'tasks' in export_options:
                toc_items.append({"title": f"{section_idx}. 任务分析", "page": page_counter})
                section_idx += 1
                page_counter += 1
                
            if 'documents' in export_options:
                toc_items.append({"title": f"{section_idx}. 文档分析", "page": page_counter})
                section_idx += 1
                page_counter += 1
                
            if 'requirements' in export_options:
                toc_items.append({"title": f"{section_idx}. 需求分析", "page": page_counter})
                section_idx += 1
                page_counter += 1
                
            if 'ai_insights' in export_options:
                toc_items.append({"title": f"{section_idx}. 风险与建议", "page": page_counter})
                section_idx += 1
                page_counter += 1
                toc_items.append({"title": f"{section_idx}. 综合结论", "page": page_counter})
            
            # 目录
            p.setFont(DEFAULT_FONT, 24)
            p.drawString(50, height-80, "目录")
            p.line(50, height-90, width-50, height-90)
            
            p.setFont(DEFAULT_FONT, 14)
            
            for i, item in enumerate(toc_items):
                p.drawString(70, height-130-30*i, item["title"])
                p.drawString(width-100, height-130-30*i, str(item["page"]))
                p.line(70, height-135-30*i, width-70, height-135-30*i)
            
            p.showPage()
            
            # 重置章节计数器，用于实际内容的创建
            section_idx = 1
            
            # 1. 项目概况
            if 'project_info' in export_options:
                y = height - 60
                y = draw_section_title(p, f"{section_idx}. 项目概况", 50, y)
                section_idx += 1
                
                p.setFont(DEFAULT_FONT, 12)
                project_info = [
                    f"项目名称：{project.name}",
                    f"项目描述：{getattr(project, 'desc', '') or '无'}",
                    f"项目状态：{getattr(project, 'status', '') or '未知'}",
                    f"起止时间：{getattr(project, 'start', '') or '未设置'} ~ {getattr(project, 'end', '') or '未设置'}",
                    f"项目成员：{project.members.count()} 人",
                    f"任务总数：{tasks.count()} 个",
                    f"文档总数：{documents.count()} 个",
                    f"需求总数：{requirements.count()} 个"
                ]
                
                for info in project_info:
                    p.drawString(70, y, info)
                    y -= 24
                
                # 绘制项目健康度状态栏
                health = project_analysis.get('health', 0)
                
                y -= 20
                p.drawString(70, y, f"项目健康度：{health}分")
                y -= 30
                
                # 绘制健康度条形图
                bar_width = 400
                bar_height = 20
                p.setFillColor(HexColor("#EEEEEE"))
                p.rect(70, y, bar_width, bar_height, fill=1)
                
                # 根据健康度值选择颜色
                if health >= 80:
                    color = HexColor("#4CAF50")  # 绿色
                elif health >= 60:
                    color = HexColor("#FFC107")  # 黄色
                else:
                    color = HexColor("#F44336")  # 红色
                
                p.setFillColor(color)
                filled_width = bar_width * health / 100
                p.rect(70, y, filled_width, bar_height, fill=1)
                
                # 显示健康状态描述
                p.setFillColor(HexColor("#000000"))
                y -= 40
                health_desc = project_analysis.get('health_desc', '')
                y = draw_text_block(p, f"健康状况：{health_desc}", 70, y, width=PRINTABLE_WIDTH - 20)
                
                p.showPage()
            
            # 2. 项目健康评估 - 只有在选择了项目健康或AI洞察时显示
            if ('project_health' in export_options or 'ai_insights' in export_options) and 'project_info' in export_options:
                y = height - 60
                y = draw_section_title(p, f"{section_idx}. 项目健康评估", 50, y)
                section_idx += 1
                
                # 项目健康评估详细说明
                y = draw_subsection_title(p, "2.1 评估指标", 70, y)
                
                p.setFont(DEFAULT_FONT, 12)
                assessment_metrics = [
                    "任务进度与计划：评估项目任务的完成情况与计划进度的吻合度",
                    "资源利用率：评估项目资源的分配与使用效率",
                    "风险管理：识别并评估项目面临的主要风险",
                    "团队协作：评估团队成员之间的协作效率和沟通质量",
                    "需求完整性：评估项目需求的完整性和清晰度"
                ]
                
                y = draw_bullet_list(p, assessment_metrics, 90, y, width=PRINTABLE_WIDTH - 40)
                
                y -= 20
                y = draw_subsection_title(p, "2.2 健康度评分解释", 70, y)
                
                assessment_explanation = [
                    "90-100分：项目运行优秀，各项指标表现良好，几乎无需干预",
                    "80-89分：项目运行良好，部分指标有小幅波动，需少量关注",
                    "70-79分：项目整体稳定，但存在明显需要改进的方面",
                    "60-69分：项目运行存在一定风险，需要引起注意并采取措施",
                    "50-59分：项目存在较多问题，需要重点关注并积极干预",
                    "50分以下：项目陷入困境，多项指标严重偏离预期，需要立即干预"
                ]
                
                y = draw_bullet_list(p, assessment_explanation, 90, y, width=PRINTABLE_WIDTH - 40)
                
                # 绘制当前项目评分
                y -= 30
                p.setFont(DEFAULT_FONT, 14)
                p.drawString(70, y, f"当前项目评分: {project_analysis.get('health', 0)}分")
                
                # 根据健康度绘制不同颜色的圆点
                health = project_analysis.get('health', 0)
                if health >= 80:
                    p.setFillColor(HexColor("#4CAF50"))  # 绿色
                    status_text = "状态良好"
                elif health >= 60:
                    p.setFillColor(HexColor("#FFC107"))  # 黄色
                    status_text = "需要关注"
                else:
                    p.setFillColor(HexColor("#F44336"))  # 红色
                    status_text = "需要干预"
                
                p.circle(270, y+5, 6, fill=1)
                p.setFillColor(HexColor("#000000"))
                p.drawString(290, y, status_text)
                
                p.showPage()
            
            # 3. 任务分析
            if 'tasks' in export_options:
                y = height - 60
                y = draw_section_title(p, f"{section_idx}. 任务分析", 50, y)
                section_idx += 1
                
                # 任务状态分布
                todo = len([t for t in tasks if t.status == 'todo'])
                doing = len([t for t in tasks if t.status == 'in-progress'])
                done = len([t for t in tasks if t.status == 'done'])
                overdue = len([t for t in tasks if t.due_date and t.due_date < datetime.date.today() and t.status != 'done'])
                
                y = draw_subsection_title(p, f"{section_idx-1}.1 任务状态分布", 70, y)
                
                p.setFont(DEFAULT_FONT, 12)
                task_stats = [
                    f"总任务数: {tasks.count()} 个",
                    f"待处理任务: {todo} 个 ({round(todo/tasks.count()*100) if tasks.count() > 0 else 0}%)",
                    f"进行中任务: {doing} 个 ({round(doing/tasks.count()*100) if tasks.count() > 0 else 0}%)",
                    f"已完成任务: {done} 个 ({round(done/tasks.count()*100) if tasks.count() > 0 else 0}%)",
                    f"逾期任务: {overdue} 个 ({round(overdue/tasks.count()*100) if tasks.count() > 0 else 0}%)"
                ]
                
                for stat in task_stats:
                    p.drawString(90, y, stat)
                    y -= 20
                
                # 任务完成趋势图
                y -= 20
                y = draw_subsection_title(p, f"{section_idx-1}.2 任务完成趋势", 70, y)
                
                if trend_chart_img:
                    img_width = 400
                    img_height = 200
                    if not safe_draw_image(p, trend_chart_img, 90, y-img_height, img_width, img_height):
                        # 如果图片绘制失败，只减少一部分空间
                        y -= (img_height/2)
                    else:
                        y -= (img_height + 30)
                
                # 任务AI分析
                y = ensure_space(p, y, 300)
                y = draw_subsection_title(p, f"{section_idx-1}.3 任务分析结论", 70, y)
                
                # 从chart_analysis获取任务趋势分析
                if 'task_trend_analysis' in chart_analysis:
                    task_analysis = chart_analysis['task_trend_analysis']
                    
                    # 关键发现
                    if 'key_findings' in task_analysis and task_analysis['key_findings']:
                        p.setFont(DEFAULT_FONT, 12)
                        p.drawString(90, y, "关键发现:")
                        y -= 20
                        y = draw_bullet_list(p, task_analysis['key_findings'], 110, y, width=PRINTABLE_WIDTH - 60)
                        y -= 10
                    
                    # 建议
                    y = ensure_space(p, y, 100)
                    if 'recommendations' in task_analysis and task_analysis['recommendations']:
                        p.setFont(DEFAULT_FONT, 12)
                        p.drawString(90, y, "建议:")
                        y -= 20
                        y = draw_bullet_list(p, task_analysis['recommendations'], 110, y, width=PRINTABLE_WIDTH - 60)
                        y -= 10
                    
                    # 洞察
                    y = ensure_space(p, y, 100)
                    if 'insights' in task_analysis and task_analysis['insights']:
                        p.setFont(DEFAULT_FONT, 12)
                        p.drawString(90, y, "深度洞察:")
                        y -= 20
                        y = draw_text_block(p, task_analysis['insights'], 110, y, width=PRINTABLE_WIDTH - 60)
                else:
                    p.setFont(DEFAULT_FONT, 12)
                    p.drawString(90, y, "暂无详细的任务分析")
                
                p.showPage()
            
            # 4. 文档分析
            if 'documents' in export_options:
                y = height - 60
                y = draw_section_title(p, f"{section_idx}. 文档分析", 50, y)
                section_idx += 1
                
                y = draw_subsection_title(p, f"{section_idx-1}.1 文档统计信息", 70, y)
                
                p.setFont(DEFAULT_FONT, 12)
                p.drawString(90, y, f"文档总数：{documents.count()} 个")
                
                # 文档上传趋势图
                y -= 30
                y = draw_subsection_title(p, f"{section_idx-1}.2 文档上传趋势", 70, y)
                
                if doc_trend_img:
                    img_width = 400
                    img_height = 200
                    if not safe_draw_image(p, doc_trend_img, 90, y-img_height, img_width, img_height):
                        # 如果图片绘制失败，只减少一部分空间
                        y -= (img_height/2)
                    else:
                        y -= (img_height + 30)
                
                # 文档AI分析
                y = ensure_space(p, y, 300)
                y = draw_subsection_title(p, f"{section_idx-1}.3 文档分析结论", 70, y)
                
                # 从chart_analysis获取文档趋势分析
                if 'doc_trend_analysis' in chart_analysis:
                    doc_analysis = chart_analysis['doc_trend_analysis']
                    
                    # 关键发现
                    if 'key_findings' in doc_analysis and doc_analysis['key_findings']:
                        p.setFont(DEFAULT_FONT, 12)
                        p.drawString(90, y, "关键发现:")
                        y -= 20
                        y = draw_bullet_list(p, doc_analysis['key_findings'], 110, y, width=PRINTABLE_WIDTH - 60)
                        y -= 10
                    
                    # 建议
                    y = ensure_space(p, y, 100)
                    if 'recommendations' in doc_analysis and doc_analysis['recommendations']:
                        p.setFont(DEFAULT_FONT, 12)
                        p.drawString(90, y, "建议:")
                        y -= 20
                        y = draw_bullet_list(p, doc_analysis['recommendations'], 110, y, width=PRINTABLE_WIDTH - 60)
                        y -= 10
                    
                    # 洞察
                    y = ensure_space(p, y, 100)
                    if 'insights' in doc_analysis and doc_analysis['insights']:
                        p.setFont(DEFAULT_FONT, 12)
                        p.drawString(90, y, "深度洞察:")
                        y -= 20
                        y = draw_text_block(p, doc_analysis['insights'], 110, y, width=PRINTABLE_WIDTH - 60)
                else:
                    p.setFont(DEFAULT_FONT, 12)
                    p.drawString(90, y, "暂无详细的文档分析")
                
                p.showPage()
            
            # 5. 需求分析
            if 'requirements' in export_options:
                y = height - 60
                y = draw_section_title(p, f"{section_idx}. 需求分析", 50, y)
                section_idx += 1
                
                y = draw_subsection_title(p, f"{section_idx-1}.1 需求统计信息", 70, y)
                
                # 优先级统计
                high_priority = len([r for r in requirements if r.priority == 'high'])
                medium_priority = len([r for r in requirements if r.priority == 'medium'])
                low_priority = len([r for r in requirements if r.priority == 'low'])
                completed_req = len([r for r in requirements if r.status == 'done'])
                
                p.setFont(DEFAULT_FONT, 12)
                req_stats = [
                    f"需求总数: {requirements.count()} 个",
                    f"高优先级: {high_priority} 个 ({round(high_priority/requirements.count()*100) if requirements.count() > 0 else 0}%)",
                    f"中优先级: {medium_priority} 个 ({round(medium_priority/requirements.count()*100) if requirements.count() > 0 else 0}%)",
                    f"低优先级: {low_priority} 个 ({round(low_priority/requirements.count()*100) if requirements.count() > 0 else 0}%)",
                    f"已完成需求: {completed_req} 个 ({round(completed_req/requirements.count()*100) if requirements.count() > 0 else 0}%)"
                ]
                
                for stat in req_stats:
                    p.drawString(90, y, stat)
                    y -= 20
                
                # 需求图表
                y -= 20
                y = draw_subsection_title(p, f"{section_idx-1}.2 需求优先级分布", 70, y)
                
                # 左侧：优先级分布图
                if req_chart_img:
                    img_width = 250
                    img_height = 180
                    safe_draw_image(p, req_chart_img, 90, y-img_height, img_width, img_height)
                
                # 右侧：需求完成率仪表盘
                if gauge_chart_img:
                    img_width = 250
                    img_height = 180
                    safe_draw_image(p, gauge_chart_img, 340, y-img_height, img_width, img_height)
                
                y -= (img_height + 30)
                
                # 需求AI分析
                y = ensure_space(p, y, 300)
                y = draw_subsection_title(p, f"{section_idx-1}.3 需求分析结论", 70, y)
                
                # 综合需求分析结果和chart_analysis
                p.setFont(DEFAULT_FONT, 12)
                
                # 需求完整性评分
                completeness = req_analysis.get('completeness', 0)
                p.drawString(90, y, f"需求完整性评分: {completeness}分")
                y -= 20
                
                # 依赖关系与冲突
                dependencies = req_analysis.get('dependencies', 0)
                conflicts = req_analysis.get('conflicts', 0)
                p.drawString(90, y, f"潜在依赖关系: {dependencies}个")
                y -= 20
                p.drawString(90, y, f"可能存在冲突: {conflicts}个")
                y -= 30
                
                # 从chart_analysis获取需求分析
                if 'req_priority_analysis' in chart_analysis and 'req_completion_analysis' in chart_analysis:
                    # 合并两个分析的关键发现
                    key_findings = []
                    if 'key_findings' in chart_analysis['req_priority_analysis']:
                        key_findings.extend(chart_analysis['req_priority_analysis']['key_findings'])
                    if 'key_findings' in chart_analysis['req_completion_analysis']:
                        key_findings.extend(chart_analysis['req_completion_analysis']['key_findings'])
                    
                    # 合并建议
                    recommendations = []
                    if 'recommendations' in chart_analysis['req_priority_analysis']:
                        recommendations.extend(chart_analysis['req_priority_analysis']['recommendations'])
                    if 'recommendations' in chart_analysis['req_completion_analysis']:
                        recommendations.extend(chart_analysis['req_completion_analysis']['recommendations'])
                    
                    # 显示关键发现
                    if key_findings:
                        p.drawString(90, y, "关键发现:")
                        y -= 20
                        y = draw_bullet_list(p, key_findings[:5], 110, y, width=PRINTABLE_WIDTH - 60)  # 限制显示最多5条
                        y -= 10
                    
                    # 显示建议
                    y = ensure_space(p, y, 100)
                    if recommendations:
                        p.drawString(90, y, "建议:")
                        y -= 20
                        y = draw_bullet_list(p, recommendations[:5], 110, y, width=PRINTABLE_WIDTH - 60)  # 限制显示最多5条
                
                # 如果还没有chart_analysis数据，则显示需求分析的建议
                elif 'suggestions' in req_analysis and req_analysis['suggestions']:
                    p.drawString(90, y, "建议:")
                    y -= 20
                    y = draw_bullet_list(p, req_analysis['suggestions'], 110, y, width=PRINTABLE_WIDTH - 60)
                
                p.showPage()
            
            # 6. 风险与建议
            if 'ai_insights' in export_options:
                y = height - 60
                y = draw_section_title(p, f"{section_idx}. 风险与建议", 50, y)
                section_idx += 1
                
                y = draw_subsection_title(p, f"{section_idx-1}.1 主要风险点", 70, y)
                
                # 显示项目分析的风险点
                risks = project_analysis.get('risks', [])
                if risks:
                    y = draw_bullet_list(p, risks, 90, y, spacing=24, width=PRINTABLE_WIDTH - 40)
                else:
                    p.setFont(DEFAULT_FONT, 12)
                    p.drawString(90, y, "未检测到明显的风险点")
                    y -= 20
                
                y -= 20
                y = draw_subsection_title(p, f"{section_idx-1}.2 AI建议措施", 70, y)
                
                # 合并所有分析的建议
                all_recommendations = []
                
                # 从需求分析获取建议
                if 'suggestions' in req_analysis:
                    all_recommendations.extend(req_analysis['suggestions'])
                
                # 从各个图表分析中获取建议
                for analysis_key in ['doc_trend_analysis', 'req_priority_analysis', 'req_completion_analysis', 'task_trend_analysis']:
                    if analysis_key in chart_analysis and 'recommendations' in chart_analysis[analysis_key]:
                        all_recommendations.extend(chart_analysis[analysis_key]['recommendations'])
                
                # 去重
                unique_recommendations = []
                for rec in all_recommendations:
                    if rec not in unique_recommendations:
                        unique_recommendations.append(rec)
                
                # 显示建议
                if unique_recommendations:
                    y = draw_bullet_list(p, unique_recommendations, 90, y, spacing=24, width=PRINTABLE_WIDTH - 40)
                else:
                    p.setFont(DEFAULT_FONT, 12)
                    p.drawString(90, y, "未提供具体建议")
                    y -= 20
                
                p.showPage()
                
                # 7. 综合结论
                y = height - 60
                y = draw_section_title(p, f"{section_idx}. 综合结论", 50, y)
                section_idx += 1
                
                # 综合项目健康状况
                p.setFont(DEFAULT_FONT, 14)
                p.setFillColor(HexColor("#1E88E5"))
                p.drawString(70, y, f"项目总体健康度: {project_analysis.get('health', 0)}分")
                p.setFillColor(HexColor("#000000"))
                y -= 30
                
                p.setFont(DEFAULT_FONT, 12)
                y = draw_text_block(p, f"健康状况: {project_analysis.get('health_desc', '')}", 70, y, width=PRINTABLE_WIDTH-20)
                y -= 30
                
                # 生成综合结论
                conclusion_prompt = f"""
                请根据以下项目数据生成一段简洁的项目综合结论(200字以内):
                
                项目名称: {project.name}
                项目描述: {getattr(project, 'desc', '') or '无描述'}
                健康度: {project_analysis.get('health', 0)}分
                健康状况: {project_analysis.get('health_desc', '')}
                任务总数: {tasks.count()}, 已完成: {done}, 进行中: {doing}, 待处理: {todo}, 逾期: {overdue}
                需求总数: {requirements.count()}, 已完成: {completed_req}
                文档总数: {documents.count()}
                
                主要风险:
                {', '.join(risks[:3]) if risks else '无明显风险'}
                
                输出格式:
                项目综合结论(不要包含标题，直接输出结论文本)
                """
                
                try:
                    # 使用AI服务生成综合结论
                    from langchain.prompts import PromptTemplate
                    prompt_template = PromptTemplate(input_variables=['input'], template="{input}")
                    chain = prompt_template | ai_service.llm
                    result = chain.invoke({"input": conclusion_prompt})
                    conclusion_text = result.content if hasattr(result, 'content') else str(result)
                    
                    # 绘制综合结论
                    y = draw_text_block(p, conclusion_text, 70, y, width=PRINTABLE_WIDTH-20, spacing=20)
                except Exception as e:
                    logger.error(f"生成综合结论失败: {e}")
                    p.drawString(70, y, "由于技术原因，无法生成综合结论。请参考前述章节的分析结果。")
                    y -= 30
                
                # 添加结尾
                y -= 30
                p.setFillColor(HexColor("#1E88E5"))
                p.setFont(DEFAULT_FONT, 14)
                p.drawString(70, y, "报告说明")
                p.setFillColor(HexColor("#000000"))
                y -= 25
                
                report_notes = [
                    "本报告由系统AI自动生成，仅供参考。",
                    "建议结合实际情况和专业判断来解读报告内容。",
                    f"报告生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
                ]
                
                p.setFont(DEFAULT_FONT, 10)
                for note in report_notes:
                    p.drawString(70, y, note)
                    y -= 20
                
                p.showPage()
            
            p.save()
            buffer.seek(0)
            
            logger.info(f"PDF生成成功: {buffer.getbuffer().nbytes}字节")
            pdf_bytes = buffer.getvalue()
            response = Response(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{project.name}_AI分析报告.pdf"'
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            return response
            
        except Exception as e:
            logger.error(f"PDF生成失败: {e}")
            logger.error(traceback.format_exc())
            return Response({
                "error": f"生成PDF时发生错误: {str(e)}",
                "detail": traceback.format_exc()
            }, status=500)

    @action(detail=True, methods=['get'])
    def chart_analysis(self, request, pk=None):
        """
        获取项目报表中每个图表的AI分析
        """
        try:
            project = self.get_object()
            
            # 获取项目相关数据
            tasks = Task.objects.filter(project=project)
            documents = ProjectDocument.objects.filter(project=project)
            requirements = Requirement.objects.filter(project=project)
            
            # 初始化AI服务
            ai_service = AIService()
            if not ai_service.is_available():
                return Response({"error": "AI服务不可用"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
            # 使用langchain进行分析
            from langchain.prompts import PromptTemplate
            from langchain_core.output_parsers import JsonOutputParser
            from pydantic import BaseModel, Field
            from typing import List
            
            # 定义输出模型
            class ChartAnalysis(BaseModel):
                key_findings: List[str] = Field(description="图表的关键发现")
                recommendations: List[str] = Field(description="基于图表数据的建议")
                insights: str = Field(description="深入洞察和总结")
            
            # 创建输出解析器
            parser = JsonOutputParser(pydantic_object=ChartAnalysis)
            
            # 准备数据统计
            task_stats = {
                "total": tasks.count(),
                "done": tasks.filter(status="done").count(),
                "in_progress": tasks.filter(status="in-progress").count(),
                "todo": tasks.filter(status="todo").count(),
            }
            
            doc_stats = {
                "total": documents.count(),
                "by_month": {}
            }
            
            # 统计文档按月份分布
            for doc in documents:
                if doc.uploaded_at:
                    month = doc.uploaded_at.strftime("%Y-%m")
                    if month in doc_stats["by_month"]:
                        doc_stats["by_month"][month] += 1
                    else:
                        doc_stats["by_month"][month] = 1
            
            req_stats = {
                "total": requirements.count(),
                "high_priority": requirements.filter(priority="high").count(),
                "medium_priority": requirements.filter(priority="medium").count(),
                "low_priority": requirements.filter(priority="low").count(),
                "completed": requirements.filter(status="done").count(),
            }
            
            # 分析文档上传趋势
            doc_trend_prompt = PromptTemplate(
                template="""
                作为一名数据分析专家，请分析以下项目的文档上传趋势数据:
                
                项目名称: {project_name}
                项目描述: {project_desc}
                
                文档统计:
                - 总文档数: {doc_total}
                - 按月份分布: {doc_by_month}
                
                请提供对文档上传趋势的分析，包括关键发现、建议和洞察。
                {format_instructions}
                """,
                input_variables=["project_name", "project_desc", "doc_total", "doc_by_month"],
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )
            
            doc_trend_chain = doc_trend_prompt | ai_service.llm | parser
            
            doc_trend_analysis = doc_trend_chain.invoke({
                "project_name": project.name,
                "project_desc": project.desc or "无描述",
                "doc_total": doc_stats["total"],
                "doc_by_month": doc_stats["by_month"]
            })
            
            # 分析需求优先级分布
            req_priority_prompt = PromptTemplate(
                template="""
                作为一名项目管理专家，请分析以下项目的需求优先级分布数据:
                
                项目名称: {project_name}
                项目描述: {project_desc}
                
                需求统计:
                - 总需求数: {req_total}
                - 高优先级: {high_priority}
                - 中优先级: {medium_priority}
                - 低优先级: {low_priority}
                
                请提供对需求优先级分布的分析，包括关键发现、建议和洞察。
                {format_instructions}
                """,
                input_variables=["project_name", "project_desc", "req_total", "high_priority", "medium_priority", "low_priority"],
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )
            
            req_priority_chain = req_priority_prompt | ai_service.llm | parser
            
            req_priority_analysis = req_priority_chain.invoke({
                "project_name": project.name,
                "project_desc": project.desc or "无描述",
                "req_total": req_stats["total"],
                "high_priority": req_stats["high_priority"],
                "medium_priority": req_stats["medium_priority"],
                "low_priority": req_stats["low_priority"]
            })
            
            # 分析需求完成率
            req_completion_prompt = PromptTemplate(
                template="""
                作为一名需求分析师，请分析以下项目的需求完成率数据:
                
                项目名称: {project_name}
                项目描述: {project_desc}
                
                需求统计:
                - 总需求数: {req_total}
                - 已完成需求: {req_completed}
                - 完成率: {completion_rate}%
                
                请提供对需求完成率的分析，包括关键发现、建议和洞察。
                {format_instructions}
                """,
                input_variables=["project_name", "project_desc", "req_total", "req_completed", "completion_rate"],
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )
            
            completion_rate = 0
            if req_stats["total"] > 0:
                completion_rate = round(req_stats["completed"] / req_stats["total"] * 100)
                
            req_completion_chain = req_completion_prompt | ai_service.llm | parser
            
            req_completion_analysis = req_completion_chain.invoke({
                "project_name": project.name,
                "project_desc": project.desc or "无描述",
                "req_total": req_stats["total"],
                "req_completed": req_stats["completed"],
                "completion_rate": completion_rate
            })
            
            # 分析任务完成趋势
            task_trend_prompt = PromptTemplate(
                template="""
                作为一名项目管理专家，请分析以下项目的任务完成趋势数据:
                
                项目名称: {project_name}
                项目描述: {project_desc}
                
                任务统计:
                - 总任务数: {task_total}
                - 已完成任务: {task_done}
                - 进行中任务: {task_in_progress}
                - 待处理任务: {task_todo}
                
                请提供对任务完成趋势的分析，包括关键发现、建议和洞察。
                {format_instructions}
                """,
                input_variables=["project_name", "project_desc", "task_total", "task_done", "task_in_progress", "task_todo"],
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )
            
            task_trend_chain = task_trend_prompt | ai_service.llm | parser
            
            task_trend_analysis = task_trend_chain.invoke({
                "project_name": project.name,
                "project_desc": project.desc or "无描述",
                "task_total": task_stats["total"],
                "task_done": task_stats["done"],
                "task_in_progress": task_stats["in_progress"],
                "task_todo": task_stats["todo"]
            })
            
            # 返回所有分析结果
            return Response({
                "doc_trend_analysis": doc_trend_analysis,
                "req_priority_analysis": req_priority_analysis,
                "req_completion_analysis": req_completion_analysis,
                "task_trend_analysis": task_trend_analysis
            })
            
        except Exception as e:
            logger.error(f"项目图表AI分析失败: {e}", exc_info=True)
            return Response({"error": f"分析失败: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProjectMemberViewSet(viewsets.ModelViewSet):
    queryset = ProjectMember.objects.all()
    serializer_class = ProjectMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 只返回当前用户能看到的项目成员
        user = self.request.user
        queryset = ProjectMember.objects.all()
        
        if user.company:
            queryset = queryset.filter(project__company=user.company)
            
        # 按项目过滤
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # 使用Python处理去重，而不是依赖数据库distinct
        # 查询所有符合条件的记录
        members = list(queryset)
        if members:
            # 优先保留全局项目成员，排除任务特定成员
            result = []
            processed_users = set()  # 已处理的用户ID
            
            # 首先添加全局成员（task为空的）
            for member in members:
                if member.task is None and member.user_id not in processed_users:
                    result.append(member)
                    processed_users.add(member.user_id)
            
            # 然后添加任务特定成员（仅当该用户没有全局成员记录时）
            for member in members:
                if member.task is not None and member.user_id not in processed_users:
                    result.append(member)
                    processed_users.add(member.user_id)
            
            # 创建一个包含这些结果的新查询集
            if result:
                return ProjectMember.objects.filter(id__in=[m.id for m in result])
            return ProjectMember.objects.none()
        
        return queryset

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.all()
        if user.company:
            queryset = queryset.filter(project__company=user.company)
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset
        
    def create(self, request, *args, **kwargs):
        """创建任务时处理日期格式问题"""
        data = request.data.copy()
        
        # 处理日期格式
        if 'due_date' in data and data['due_date']:
            try:
                # 尝试转换各种可能的日期格式为YYYY-MM-DD
                import datetime
                from dateutil import parser
                
                date_str = data['due_date']
                # 如果是时间戳
                if isinstance(date_str, (int, float)) or (isinstance(date_str, str) and date_str.isdigit()):
                    date_obj = datetime.datetime.fromtimestamp(float(date_str)/1000)
                else:
                    # 尝试解析其他日期格式
                    date_obj = parser.parse(date_str)
                
                # 转换为YYYY-MM-DD格式
                data['due_date'] = date_obj.strftime('%Y-%m-%d')
            except Exception as e:
                logger.error(f"日期格式转换失败: {e}")
                # 如果转换失败，不修改原始数据
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
    def perform_create(self, serializer):
        # 自动设置创建者为当前用户
        if self.request.user.is_authenticated:
            serializer.save(creator=self.request.user)
        else:
            serializer.save()
            
        data = self.request.data
        logger.info(f"创建任务请求数据: {data}")
        assignee_id = data.get('assignee_id')
        project_id = data.get('project')
        # 先保存任务，拿到 task 实例
        task = serializer.instance # perform_create之前已经保存，直接获取实例
        assignee_member = None
        assignee_user = None
        if assignee_id and project_id:
            try:
                assignee_user = User.objects.get(id=assignee_id)
                project = Project.objects.get(id=project_id)
                # 确保用户是项目成员
                if assignee_user not in project.members.all():
                    project.members.add(assignee_user)
                # 查找或创建负责人的全局项目成员记录(不带task)
                global_member, created = ProjectMember.objects.get_or_create(
                    user=assignee_user,
                    project=project,
                    task__isnull=True,  # 全局项目成员
                    defaults={'role': '成员'}
                )
                # 查找/新建 负责人 ProjectMember（与当前任务绑定）
                assignee_member, created = ProjectMember.objects.get_or_create(
                    user=assignee_user, 
                    project=project, 
                    task=task,
                    defaults={'role': '负责人'}
                )
                if not created and assignee_member.role != '负责人':
                    assignee_member.role = '负责人'
                    assignee_member.save(update_fields=['role'])
                
                # 更新任务的 assignee 字段为该 ProjectMember
                task.assignee = assignee_member
                task.save(update_fields=['assignee'])
            except Exception as e:
                logger.error(f"设置任务负责人失败: {e}")
        
        # 其它项目成员都作为成员身份与任务绑定
        if task and task.project:
            # 获取所有项目成员，跳过负责人
            project_users = [user for user in task.project.members.all() 
                         if not (assignee_user and user.id == assignee_user.id)]
            
            # 为项目成员创建任务成员记录和完成记录
            for u in project_users:
                # 确保用户有全局项目成员记录
                global_member, _ = ProjectMember.objects.get_or_create(
                    user=u, 
                    project=task.project,
                    task__isnull=True,  # 全局项目成员
                    defaults={'role': '成员'}
                )
                
                # 创建或获取任务特定的项目成员记录
                task_member, _ = ProjectMember.objects.get_or_create(
                    user=u,
                    project=task.project,
                    task=task,
                    defaults={'role': '成员'}
                )
                
                # 创建任务完成记录
                TaskCompletion.objects.get_or_create(task=task, member=task_member)
            
            # 确保负责人也有任务完成记录
            if assignee_member:
                TaskCompletion.objects.get_or_create(task=task, member=assignee_member)

    def perform_update(self, serializer):
        task = serializer.save()
        # 同步 Project.members 到 ProjectMember
        if task and task.project:
            # 为每个项目成员创建全局成员记录(非任务特定)
            for user in task.project.members.all():
                ProjectMember.objects.get_or_create(
                    user=user, 
                    project=task.project,
                    task__isnull=True,  # 全局记录
                    defaults={'role': '成员'}
                )
            
            # 确保有任务完成记录
            # 只获取全局项目成员(无任务关联)或当前任务的成员，避免获取其他任务的成员
            relevant_members = ProjectMember.objects.filter(
                project=task.project
            ).filter(
                models.Q(task__isnull=True) | models.Q(task=task)
            ).distinct()
            
            # 为相关成员创建任务完成记录
            for member in relevant_members:
                # 跳过任务特定的成员记录(非当前任务)
                if member.task is not None and member.task != task:
                    continue
                    
                # 为全局成员创建任务特定记录
                if member.task is None:
                    task_member, _ = ProjectMember.objects.get_or_create(
                        user=member.user,
                        project=task.project,
                        task=task,
                        defaults={'role': '成员' if task.assignee and task.assignee.user != member.user else '负责人'}
                    )
                    TaskCompletion.objects.get_or_create(task=task, member=task_member)
                else:
                    # 已有任务特定记录，直接创建完成记录
                    TaskCompletion.objects.get_or_create(task=task, member=member)

    def update(self, request, *args, **kwargs):
        data = request.data.copy()
        assignee_id = data.get('assignee_id')
        project_id = data.get('project')
        if assignee_id and project_id:
            try:
                user = User.objects.get(id=assignee_id)
                project = Project.objects.get(id=project_id)
                project_member, created = ProjectMember.objects.get_or_create(
                    user=user,
                    project=project,
                    defaults={'role': '成员'}
                )
                if created:
                    logger.info(f"自动创建项目成员: 用户={user.username}, 项目={project.name}")
                data['assignee'] = project_member.id
                data.pop('assignee_id', None)
                logger.info(f"成功设置任务负责人: {project_member}")
            except User.DoesNotExist:
                logger.error(f"用户ID {assignee_id} 不存在")
            except Project.DoesNotExist:
                logger.error(f"项目ID {project_id} 不存在")
            except Exception as e:
                logger.error(f"更新任务负责人失败: {e}")
        # 处理日期格式
        if 'due_date' in data and data['due_date']:
            try:
                import datetime
                from dateutil import parser
                date_str = data['due_date']
                if isinstance(date_str, (int, float)) or (isinstance(date_str, str) and date_str.isdigit()):
                    date_obj = datetime.datetime.fromtimestamp(float(date_str)/1000)
                else:
                    date_obj = parser.parse(date_str)
                data['due_date'] = date_obj.strftime('%Y-%m-%d')
            except Exception as e:
                logger.error(f"日期格式转换失败: {e}")
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def ai_analysis(self, request, pk=None):
        """任务AI分析接口"""
        task = self.get_object()
        ai_service = AIService()
        
        if not ai_service.is_available():
            return Response({
                "error": "AI服务不可用，请检查配置"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        suggestions = ai_service.analyze_task(task)
        
        return Response({
            "suggestions": suggestions
        })

class ProjectDocumentViewSet(mixins.CreateModelMixin,
                             mixins.ListModelMixin,
                             mixins.DestroyModelMixin,
                             mixins.UpdateModelMixin,
                             viewsets.GenericViewSet):
    queryset = ProjectDocument.objects.all().order_by('-uploaded_at')
    serializer_class = ProjectDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def perform_create(self, serializer):
        serializer.save(uploader=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset 
    
    @action(detail=False, methods=['get'])
    def ai_dashboard(self, request):
        """文档AI仪表盘分析接口"""
        project_id = request.query_params.get('project')
        if not project_id:
            return Response({"error": "缺少项目ID参数"}, status=status.HTTP_400_BAD_REQUEST)
            
        documents = ProjectDocument.objects.filter(project_id=project_id)
        if not documents.exists():
            return Response({
                "health_score": 0,
                "health_desc": "未找到文档",
                "related_count": 0,
                "conflict_count": 0,
                "suggestions": ["当前项目尚未上传文档，无法进行分析"]
            })
            
        ai_service = AIService()
        if not ai_service.is_available():
            # 返回模拟数据
            return Response({
                "health_score": 70,
                "health_desc": "文档质量一般，建议完善",
                "related_count": min(documents.count(), 5),
                "conflict_count": min(documents.count() // 3, 2),
                "suggestions": [
                    "AI服务不可用，这是模拟数据",
                    "建议整理文档结构",
                    "文档版本管理需要改进"
                ]
            })
        
        # 实际调用AI分析
        try:
            # 构建文档分析提示
            doc_info = "\n".join([
                f"文档{i+1}. {doc.name}: {doc.desc or '无描述'}" 
                for i, doc in enumerate(documents[:10])  # 最多取前10个文档
            ])
            
            prompt = f"""
            请分析以下项目文档列表，并提供以下指标:
            {doc_info}
            
            请提供:
            1. 文档健康度评分(0-100的整数)
            2. 文档健康度描述(一句话)
            3. 相互关联的文档数量(估计值)
            4. 可能存在内容冲突的文档数量(估计值)
            5. 2-3条关于文档管理的建议
            
            按照以下格式返回:
            健康度: 分数
            健康描述: xxx
            相关文档: 数量
            冲突文档: 数量
            建议1: xxx
            建议2: xxx
            """
            
            chain = ConversationChain(llm=ai_service.llm)
            result = chain.invoke({"input": prompt})
            
            # 解析结果
            lines = result.content.strip().split('\n')
            health_score = 0
            health_desc = "文档状态未知"
            related_count = 0
            conflict_count = 0
            suggestions = []
            
            for line in lines:
                if line.startswith("健康度:"):
                    try:
                        health_score = int(line.split(":", 1)[1].strip())
                    except:
                        health_score = 70
                elif line.startswith("健康描述:"):
                    health_desc = line.split(":", 1)[1].strip()
                elif line.startswith("相关文档:"):
                    try:
                        related_count = int(line.split(":", 1)[1].strip())
                    except:
                        related_count = min(documents.count(), 5)
                elif line.startswith("冲突文档:"):
                    try:
                        conflict_count = int(line.split(":", 1)[1].strip())
                    except:
                        conflict_count = min(documents.count() // 3, 2)
                elif line.startswith("建议"):
                    suggestion = line.split(":", 1)[1].strip() if ":" in line else line
                    suggestions.append(suggestion)
            
            # 确保有默认值
            if not suggestions:
                suggestions = ["建议优化文档分类", "考虑添加文档之间的引用关系"]
            
            return Response({
                "health_score": health_score,
                "health_desc": health_desc,
                "related_count": related_count,
                "conflict_count": conflict_count,
                "suggestions": suggestions
            })
        except Exception as e:
            logger.error(f"文档AI分析失败: {e}")
            # 出错时返回基础分析数据
            return Response({
                "health_score": 65,
                "health_desc": "文档状态一般",
                "related_count": min(documents.count(), 3),
                "conflict_count": min(documents.count() // 4, 1),
                "suggestions": ["AI分析过程中出现错误，这是估算数据", "建议完善文档管理"]
            })
    
    @action(detail=True, methods=['post'])
    def ai_analyze(self, request, pk=None):
        """文档AI分析接口"""
        document = self.get_object()
        ai_service = AIService()
        
        if not ai_service.is_available():
            return Response({
                "error": "AI服务不可用，请检查配置"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        analysis = ai_service.analyze_document(document)
        
        # 将AI分析结果保存到文档记录中
        document.analysis = analysis
        document.save(update_fields=['analysis'])
        
        return Response({
            "analysis": analysis
            })

class TaskCompletionViewSet(viewsets.ModelViewSet):
    queryset = TaskCompletion.objects.all()
    serializer_class = TaskCompletionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        # 用户只能看到自己公司内的任务完成记录
        if user.company:
            queryset = queryset.filter(member__project__company=user.company)
        # 过滤指定任务的完成记录
        task_id = self.request.query_params.get('task')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        # 添加排序，解决分页警告
        return queryset.order_by('id')

class RequirementViewSet(viewsets.ModelViewSet):
    """需求管理视图集"""
    queryset = Requirement.objects.all().order_by('-created_at')
    serializer_class = RequirementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取需求列表，可按项目过滤"""
        user = self.request.user
        queryset = Requirement.objects.all()
        
        # 用户只能看到自己公司内的需求
        if user.company:
            queryset = queryset.filter(project__company=user.company)
            
        # 按项目过滤
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
            
        return queryset
    
    def perform_create(self, serializer):
        """创建需求时自动设置创建者为当前用户"""
        serializer.save(creator=self.request.user)
        
    @action(detail=False, methods=['get'], url_path='ai_analysis')
    def ai_analysis_all(self, request):
        """需求AI分析接口 - 增强实现"""
        project_id = request.query_params.get('project')
        if not project_id:
            return Response({"error": "缺少项目ID参数"}, status=status.HTTP_400_BAD_REQUEST)
            
        # 获取项目下的所有需求
        requirements = Requirement.objects.filter(project_id=project_id)
        if not requirements.exists():
            return Response({
                "completeness": 0,
                "dependencies": 0,
                "conflicts": 0,
                "suggestions": ["当前项目尚未创建需求，无法进行分析"]
            })
            
        ai_service = AIService()
        if not ai_service.is_available():
            # 返回模拟数据
            return Response({
                "completeness": 75,
                "dependencies": 8,
                "conflicts": 2,
                "suggestions": [
                    "AI服务不可用，这是模拟数据",
                    "建议调整需求优先级",
                    "需求分类合理"
                ]
            })
        
        try:
            # 构建需求分析提示
            req_info = "\n".join([
                f"需求{i+1}. {r.name}: {r.description or '无描述'} [优先级:{r.priority}]" 
                for i, r in enumerate(requirements[:10])  # 最多取前10个需求
            ])
            
            prompt = f"""
            请分析以下项目需求列表，并提供以下指标:
            {req_info}
            请提供:
            1. 需求完整性评分(0-100的整数)
            2. 可能存在的需求依赖关系数量
            3. 可能的需求冲突数量
            4. 2-3条关于需求的建议
            按照以下格式返回:
            完整性评分: 分数
            依赖关系: 数量
            需求冲突: 数量
            建议1: xxx
            建议2: xxx
            """
            chain = ConversationChain(llm=ai_service.llm)
            result = chain.invoke({"input": prompt})
            
            # 解析结果
            lines = result.content.strip().split('\n')
            completeness = 0
            dependencies = 0
            conflicts = 0
            suggestions = []
            
            for line in lines:
                if line.startswith("完整性评分:"):
                    try:
                        completeness = int(line.split(":", 1)[1].strip())
                    except:
                        completeness = 70
                elif line.startswith("依赖关系:"):
                    try:
                        dependencies = int(line.split(":", 1)[1].strip())
                    except:
                        dependencies = 5
                elif line.startswith("需求冲突:"):
                    try:
                        conflicts = int(line.split(":", 1)[1].strip())
                    except:
                        conflicts = 2
                elif line.startswith("建议"):
                    suggestion = line.split(":", 1)[1].strip() if ":" in line else line
                    suggestions.append(suggestion)
            
            # 确保有默认值
            if not suggestions:
                suggestions = ["建议优化需求描述，增加细节", "考虑按功能对需求进行分类"]
            
            return Response({
                "completeness": completeness,
                "dependencies": dependencies,
                "conflicts": conflicts,
                "suggestions": suggestions
            })
        except Exception as e:
            logger.error(f"需求AI分析失败: {e}")
            # 出错时返回基础分析数据
            return Response({
                "completeness": 70,
                "dependencies": len(requirements) // 2,  # 简单估算
                "conflicts": min(2, len(requirements) // 5),
                "suggestions": ["AI分析过程中出现错误，这是估算数据", "建议完善需求描述"]
            })

    @action(detail=True, methods=['get'])
    def ai_analysis(self, request, pk=None):
        """单条需求AI分析接口"""
        requirement = self.get_object()
        ai_service = AIService()
        if not ai_service.is_available():
            return Response({"ai_analysis": "AI服务不可用"}, status=500)
        try:
            result = ai_service.analyze_requirement([requirement])
            suggestions = result.get("suggestions", [])
            text = "；".join(suggestions) if suggestions else "暂无分析"
            return Response({"ai_analysis": text})
        except Exception as e:
            logger.error(f"单条需求AI分析失败: {e}", exc_info=True)
            return Response({"ai_analysis": "AI分析失败"}, status=500) 