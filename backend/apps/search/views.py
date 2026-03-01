from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
import logging
from django.utils.html import strip_tags

# 导入所有需要搜索的模型
from apps.project.models import Project, Task, Requirement, ProjectDocument
from apps.calendar.models import CalendarEvent
from apps.smartdoc.models import Document as SmartDoc
from apps.contract.models import Contract, ContractTemplate
from apps.knowledge.models import KnowledgeBase, KnowledgeChunk
from apps.ai.models import AIChatMessage
from django.contrib.auth import get_user_model

from .serializers import GlobalSearchResultSerializer

User = get_user_model()
logger = logging.getLogger(__name__)

class GlobalSearchView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 2:
            return Response({"error": "搜索查询至少需要2个字符"}, status=400)

        user = request.user
        results = []

        # 1. 搜索项目 (Project, Task, Requirement, ProjectDocument)
        try:
            # 搜索项目
            projects = Project.objects.filter(
                Q(company=user.company) & (Q(name__icontains=query) | Q(desc__icontains=query))
            )
            for p in projects:
                results.append({
                    'type': '项目', 'id': p.id, 'title': p.name,
                    'summary': strip_tags(p.desc) if p.desc else '无描述',
                    'url': f'/project/{p.id}',
                    'meta': {'creator': p.company.name, 'created_at': p.start}
                })

            # 搜索任务
            tasks = Task.objects.filter(
                Q(project__company=user.company) & (Q(title__icontains=query) | Q(description__icontains=query))
            )
            for t in tasks:
                results.append({
                    'type': '任务', 'id': t.id, 'title': t.title,
                    'summary': strip_tags(t.description) if t.description else '无描述',
                    'url': f'/project/{t.project.id}?tab=tasks',
                    'meta': {'creator': t.project.name, 'created_at': t.due_date}
                })
        except Exception as e:
            logger.error(f"搜索项目模块失败: {e}")

        # 2. 搜索日历事件 (CalendarEvent)
        try:
            events = CalendarEvent.objects.filter(
                Q(creator=user) | Q(participants=user)
            ).filter(
                Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query)
            ).distinct()
            for e in events:
                results.append({
                    'type': '日程', 'id': e.id, 'title': e.title,
                    'summary': strip_tags(e.description) if e.description else e.location or '无描述',
                    'url': '/calendar/index',
                    'meta': {'creator': e.creator.username, 'created_at': e.start}
                })
        except Exception as e:
            logger.error(f"搜索日历模块失败: {e}")
            
        # 3. 搜索智能文档 (SmartDoc)
        try:
            smart_docs = SmartDoc.objects.filter(creator=user).filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            )
            for d in smart_docs:
                results.append({
                    'type': '智能文档', 'id': d.id, 'title': d.title,
                    'summary': strip_tags(d.get_preview()),
                    'url': f'/smartdoc/{d.id}',
                    'meta': {'creator': d.creator.username, 'created_at': d.created_at}
                })
        except Exception as e:
            logger.error(f"搜索智能文档模块失败: {e}")

        # 4. 搜索合同 (Contract, ContractTemplate)
        try:
            contracts = Contract.objects.filter(created_by__company=user.company).filter(
                Q(title__icontains=query) | Q(content__icontains=query) | Q(number__icontains=query)
            )
            for c in contracts:
                summary_text = strip_tags(c.content) if c.content else '无内容'
                summary_preview = summary_text[:100] + '...' if len(summary_text) > 100 else summary_text
                results.append({
                    'type': '合同', 'id': c.id, 'title': c.title,
                    'summary': summary_preview,
                    'url': f'/contract/{c.id}',
                    'meta': {'creator': c.created_by.username, 'created_at': c.created_at}
                })
        except Exception as e:
            logger.error(f"搜索合同模块失败: {e}")

        # 5. 搜索知识库 (KnowledgeBase)
        try:
            kbs = KnowledgeBase.objects.filter(company=user.company).filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
            for kb in kbs:
                results.append({
                    'type': '知识库', 'id': kb.id, 'title': kb.title,
                    'summary': strip_tags(kb.description) if kb.description else '无描述',
                    'url': f'/knowledge?kid={kb.id}',
                    'meta': {'creator': kb.creator.username if kb.creator else '', 'created_at': kb.created_at}
                })
        except Exception as e:
            logger.error(f"搜索知识库模块失败: {e}")

        # 6. 搜索聊天记录 (AIChatMessage) - 仅搜索用户自己的
        try:
            chat_messages = AIChatMessage.objects.filter(
                chat__user=user, content__icontains=query
            ).order_by('-created_at')[:10] # 限制数量
            for msg in chat_messages:
                results.append({
                    'type': '聊天记录', 'id': msg.id, 'title': f"与AI的对话: {msg.content[:20]}...",
                    'summary': msg.content,
                    'url': f'/chat?chatId={msg.chat.id}',
                    'meta': {'creator': user.username, 'created_at': msg.created_at}
                })
        except Exception as e:
            logger.error(f"搜索聊天记录失败: {e}")

        # 7. 搜索用户 (User)
        try:
            users = User.objects.filter(
                Q(company=user.company) & (Q(username__icontains=query) | Q(email__icontains=query) | Q(first_name__icontains=query))
            ).exclude(id=user.id)
            for u in users:
                results.append({
                    'type': '联系人', 'id': u.id, 'title': u.get_full_name() or u.username,
                    'summary': u.email,
                    'url': f'#/users/{u.id}', 
                    'meta': {'department': u.department.name if u.department else '无部门', 'created_at': u.date_joined}
                })
        except Exception as e:
            logger.error(f"搜索用户失败: {e}")

        # 序列化结果
        serializer = GlobalSearchResultSerializer(results, many=True)
        return Response(serializer.data)
