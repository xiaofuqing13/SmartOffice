from typing import List
import os
import yaml
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from dateutil.parser import parse as parse_datetime
from datetime import timedelta

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool

from .models import CalendarEvent

# --- 配置加载 ---
# 假设 settings.BASE_DIR 指向 Django 项目的 backend 根目录
try:
    config_path = os.path.join(settings.BASE_DIR, 'setting.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    ai_config = config.get('ai', {})
except (FileNotFoundError, AttributeError):
    # 如果文件找不到或BASE_DIR未配置，提供一个默认的回退或错误处理
    print("警告: setting.yaml 文件未找到或 Django settings.BASE_DIR 未配置。将使用环境变量或默认值。")
    ai_config = {}

# 从配置或环境变量中获取AI设置
OPENAI_API_KEY = ai_config.get('openai_api_key', os.environ.get("OPENAI_API_KEY"))
OPENAI_API_BASE = ai_config.get('openai_api_base', os.environ.get("OPENAI_API_BASE"))
MODEL_NAME = ai_config.get('model', 'Doubao-lite-128k') # 默认使用配置文件中的模型

# --- 全局用户变量 ---
# 用于在工具函数中访问当前请求的用户
_user = None

# --- 工具定义 ---
@tool
def add_event(title: str, start_time: str, end_time: str = None, location: str = None, description: str = None):
    """向日历添加一个新事件。如果未提供end_time，则默认为start_time后一小时。所有时间参数 (start_time, end_time) 都必须是 'YYYY-MM-DD HH:MM' 格式。"""
    try:
        start = parse_datetime(start_time)
        if end_time:
            end = parse_datetime(end_time)
        else:
            end = start + timedelta(hours=1)
        
        # 确保结束时间在开始时间之后
        if end <= start:
            end = start + timedelta(hours=1)

        event = CalendarEvent.objects.create(
            title=title,
            start=start,
            end=end,
            location=location,
            description=description,
            creator=_user
        )
        event.participants.add(_user)
        
        # 返回结构化的日程信息
        return {
            "message": f"事件 '{title}' 已成功创建，ID为 {event.id}。",
            "event": {
                "id": event.id,
                "title": event.title,
                "start": event.start.isoformat(),
                "end": event.end.isoformat(),
                "location": event.location,
                "description": event.description
            }
        }
    except Exception as e:
        return f"添加事件时出错: {str(e)}"

@tool
def search_events(query: str = None, start_time: str = None, end_time: str = None):
    """
    根据文本、时间或两者组合来搜索日历事件。
    - 如果提供了 'query'，将对事件的标题、描述和地点进行文本搜索。
    - 如果提供了 'start_time'，将查找该时间点所在日期的所有事件。
    - 如果同时提供了 'start_time' 和 'end_time'，将查找在该时间范围内开始的事件。
    - 所有时间参数 (start_time, end_time) 都必须是 'YYYY-MM-DD HH:MM' 格式。
    - 如果用户提到了时间（如“明天下午3点”），请优先使用 'start_time' 参数进行搜索。
    """
    try:
        queryset = CalendarEvent.objects.filter(
            Q(creator=_user) | Q(participants=_user)
        ).distinct()

        # Build time-based query if time is provided
        time_filter = Q()
        if start_time:
            # 使用dateutil.parser增强对相对时间的处理
            try:
                start_dt = parse_datetime(start_time, fuzzy=True)
            except (ValueError, TypeError):
                # 如果解析失败，返回错误提示
                return f"无法识别的时间格式: '{start_time}'。请使用更明确的时间，如 'YYYY-MM-DD HH:MM'。"

            if not end_time:
                # 如果只提供了开始时间，则搜索当天全天的日程
                start_of_day = start_dt.replace(hour=0, minute=0, second=0)
                end_of_day = start_dt.replace(hour=23, minute=59, second=59)
                time_filter = Q(start__gte=start_of_day, start__lte=end_of_day)
            else:
                # 如果提供了结束时间，则严格按范围查找
                end_dt = parse_datetime(end_time)
                time_filter = Q(start__gte=start_dt, start__lte=end_dt)
        
        # Build text-based query if text is provided
        text_filter = Q()
        if query:
            text_filter = Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query)

        # Combine queries
        if time_filter and text_filter:
            combined_queryset = queryset.filter(time_filter & text_filter)
            # If combined search has results, use it. Otherwise, fallback to time-only search.
            final_queryset = combined_queryset if combined_queryset.exists() else queryset.filter(time_filter)
        elif time_filter:
            final_queryset = queryset.filter(time_filter)
        elif text_filter:
            final_queryset = queryset.filter(text_filter)
        else:
            return "搜索失败：请提供搜索关键词或时间。"

        events = final_queryset.order_by('start')[:10]

        if not events.exists():
            return "根据您的查询，未找到相关事件。"
        
        results = {
            "message": "为您找到以下事件:",
            "events": [
                {
                    "id": event.id,
                    "title": event.title,
                    "start": event.start.strftime('%Y年%m月%d日 %H:%M'),
                    "location": event.location,
                    "description": event.description
                }
                for event in events
            ]
        }
        return results
    except Exception as e:
        return f"搜索事件时出错: {str(e)}"

@tool
def edit_event(event_id: int, title: str = None, start_time: str = None, end_time: str = None, location: str = None, description: str = None):
    """根据事件ID编辑一个现有事件。所有时间参数 (start_time, end_time) 都必须是 'YYYY-MM-DD HH:MM' 格式。"""
    try:
        event = CalendarEvent.objects.get(id=event_id, participants=_user)
        if title:
            event.title = title
        if start_time:
            event.start = parse_datetime(start_time)
        if end_time:
            event.end = parse_datetime(end_time)
        if location:
            event.location = location
        if description:
            event.description = description
        event.save()
        
        # 返回结构化的更新信息
        return {
            "message": f"ID为 {event_id} 的事件已成功更新。",
            "event": {
                "id": event.id,
                "title": event.title,
                "start": event.start.isoformat(),
                "end": event.end.isoformat(),
                "location": event.location,
                "description": event.description
            }
        }
    except CalendarEvent.DoesNotExist:
        return f"未找到ID为 {event_id} 的事件。请先使用搜索工具确认事件ID。"
    except Exception as e:
        return f"编辑事件时出错: {str(e)}"

@tool
def delete_event(event_id: int):
    """根据事件ID删除一个事件。"""
    try:
        event = CalendarEvent.objects.get(id=event_id, participants=_user)
        event_title = event.title
        event.delete()
        return f"ID为 {event_id} 的事件 '{event_title}' 已成功删除。"
    except CalendarEvent.DoesNotExist:
        return f"未找到ID为 {event_id} 的事件。请先使用搜索工具确认事件ID。"
    except Exception as e:
        return f"删除事件时出错: {str(e)}"

@tool
def delete_events(event_ids: List[int]):
    """根据事件ID列表批量删除事件。"""
    try:
        events_to_delete = CalendarEvent.objects.filter(id__in=event_ids, participants=_user)
        
        deleted_count = events_to_delete.count()
        
        if deleted_count == 0:
            return "未找到任何有权限删除的指定事件。"
            
        events_to_delete.delete()

        if deleted_count < len(event_ids):
            return f"成功删除了 {deleted_count} 个您有权限的事件。"
        else:
            return f"已成功删除 {deleted_count} 个事件。"
    except Exception as e:
        return f"批量删除事件时出错: {str(e)}"

# --- 主服务函数 (此部分已迁移至 ai/services.py) ---
# 后续可移除此处的 process_natural_language_query 函数
# def process_natural_language_query(query: str, user):
#     ... 