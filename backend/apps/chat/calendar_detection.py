"""Calendar event detection module."""
import re
from datetime import datetime, timedelta
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from django.conf import settings
import json
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

class CalendarEventInfo(BaseModel):
    """日程事件信息模型"""
    title: str = Field(description="事件标题，例如：'团队会议'或'客户拜访'")
    start_time: str = Field(description="开始时间，尽量精确到具体时间，例如：'2023-06-15 14:00'")
    end_time: str = Field(description="结束时间，尽量精确到具体时间，例如：'2023-06-15 15:30'")
    location: Optional[str] = Field(description="地点，例如：'会议室A'或'线上会议'", default=None)
    description: Optional[str] = Field(description="事件描述或详情", default=None)
    event_type: str = Field(description="事件类型，必须是以下之一：'blue'(会议)，'orange'(出差)，'green'(假期)，'red'(截止日期)，'purple'(其他)", default="blue")
    is_detected: bool = Field(description="是否成功检测到日程信息", default=False)

def detect_calendar_event(message_content):
    """
    使用LangChain检测消息中的日程事件信息
    Args:
        message_content: 消息内容
    Returns:
        CalendarEventInfo对象
    """
    try:
        # 设置默认的返回对象
        default_event = CalendarEventInfo(
            title="",
            start_time="",
            end_time="",
            location=None,
            description=None,
            event_type="blue",
            is_detected=False
        )
        
        # 如果内容为空，直接返回默认值
        if not message_content:
            return default_event
            
        # 简短消息长度要求降低为3个字符，避免错过短消息中的日程信息
        if len(message_content.strip()) < 3:
            return default_event

        # 使用pydantic解析器
        parser = PydanticOutputParser(pydantic_object=CalendarEventInfo)
        
        # 创建更精确的提示模板
        prompt = ChatPromptTemplate.from_template("""
        你是一个专业的中文日程识别助手，需要从用户的聊天消息中提取日程相关信息。

        请仔细分析以下消息内容，判断是否包含日程安排信息（如会议、约见、活动等）：
        
        ```
        {message}
        ```
        
        对于日程信息识别，请遵循以下规则：
        1. 非常宽松地识别内容，即使信息不完整也要尽量提取（只要包含时间+地点或时间+事件）
        2. 短文本消息也可能包含日程信息，例如"明天10点开会"、"下午3点Sa206"
        3. 如果没有明确的事件标题，可以根据内容推断，如"在会议室开会"→标题为"开会"
        4. 不需要消息完整才能识别，只要有有效的日程要素即可
        
        如果消息包含日程信息，请提取以下字段：
        1. 标题：事件的名称或主题，如"开会"、"团队会议"等
           - 如果没有明确标题，可从上下文推断，如"在会议室讨论"→标题为"讨论"
           - 如果只有地点和时间，可将地点作为标题的一部分，如"Sa206"→"Sa206会议"
        
        2. 开始时间：尽量精确到具体日期和时间，使用YYYY-MM-DD HH:MM格式
           - 中文时间表达：
             * "今天" = 当天日期
             * "明天" = 当天+1天
             * "后天" = 当天+2天
             * "大后天" = 当天+3天
             * "下周x" = 下周对应星期几
           - 时间段识别：
             * "上午" = 9:00-12:00，如无具体时间则默认为10:00
             * "中午" = 12:00-13:00，默认为12:00
             * "下午" = 13:00-18:00，默认为15:00
             * "晚上" = 18:00-22:00，默认为19:00
             * "凌晨/早上" = 5:00-9:00，默认为8:00
           - 具体点数：
             * "下午3点" = 15:00，"晚上8点" = 20:00
             * 数字+"点"即为对应小时，可能包含分钟如"3点15分"
        
        3. 结束时间：若未明确指定，则根据事件类型推断
           - 会议类：默认为开始时间后1小时
           - 全天活动：当天23:59
           - 如有明确结束时间词语如"到"、"至"、"-"等，使用指定的结束时间
        
        4. 地点：事件地点，如"会议室"、"Sa206"、"线上"、"一楼大厅"等
           - 识别教室编号：如Sa206、A101等格式
           - 识别常见场所：会议室、多功能厅、报告厅、教室等
           - 识别线上地点：腾讯会议、ZOOM、线上等
        
        5. 描述：事件的详细描述，可以是消息中除了标题、时间、地点外的补充说明
        
        6. 事件类型：使用以下值之一：
           - blue(会议)：会议、讨论、面试、考试、报告等
           - orange(出差)：出差、外出、拜访客户等
           - green(假期)：休假、请假、放假等
           - red(截止日期)：截止日期、提交、验收等
           - purple(其他)：其他类型活动
        
        以下是几个日程消息示例及分析：
        
        示例1: "明天上午10点在Sa206开会"
        分析:
        - 标题: "开会"
        - 开始时间: [明天]的10:00
        - 地点: "Sa206"
        - 类型: blue(会议)
        - is_detected: true
        
        示例2: "下周一下午3点项目评审"
        分析:
        - 标题: "项目评审"
        - 开始时间: [下周一]的15:00
        - 类型: blue(会议)
        - is_detected: true
        
        示例3: "记得去A101"
        分析:
        - 不包含时间信息，不构成完整日程
        - is_detected: false
        
        示例4: "11:30午餐"
        分析:
        - 标题: "午餐"
        - 开始时间: [今天]的11:30
        - 类型: purple(其他)
        - is_detected: true
        
        示例5: "明天Sa206"
        分析:
        - 标题: "Sa206会议"（推断为会议）
        - 开始时间: [明天]（无具体时间时，可默认为上午10:00）
        - 地点: "Sa206"
        - 类型: blue(会议)
        - is_detected: true
        
        当前日期是：{current_date}
        
        重要：请仅输出符合下面格式指令的、不包含任何额外解释或Markdown标记（例如 ```json）的纯JSON对象。

        {format_instructions}
        """)
        
        # 组合提示和输出解析器，添加当前日期上下文
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # 修复API调用方式
        llm = ChatOpenAI(
            temperature=0, 
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            model_name=settings.AI_MODEL
        )
        
        # 使用正确的API方法创建和执行链
        formatted_prompt = prompt.format(
            message=message_content,
            current_date=current_date,
            format_instructions=parser.get_format_instructions()
        )
        
        # 执行模型调用和解析
        try:
            llm_response = llm.invoke(formatted_prompt)
            result = parser.parse(llm_response.content)
            
            # 如果检测到日程信息，返回结果
            if result and hasattr(result, 'is_detected'):
                # 更宽松的检测标准：有标题和时间/地点信息，就认为有效
                has_title = bool(result.title)
                has_time = bool(result.start_time)
                has_location = bool(result.location)
                
                # 更新检测逻辑：
                # 1. 有标题+时间 -> 有效
                # 2. 有标题+地点 -> 有效
                # 3. 只有时间+地点，但可以从中推断标题 -> 有效
                result.is_detected = (has_title and (has_time or has_location))
                
                # 如果没有标题但有地点，以地点命名会议
                if not has_title and has_location and has_time:
                    result.title = f"{result.location}会议"
                    result.is_detected = True
                
                # 如果检测到日程但没有事件类型，根据内容设置默认类型
                if result.is_detected and not result.event_type:
                    # 检查标题或描述中是否包含会议相关词语
                    content = (result.title + " " + (result.description or "")).lower()
                    
                    # 扩充关键词识别
                    meeting_keywords = ["会议", "开会", "会", "讨论", "评审", "汇报", "面试", "演讲", "报告", "培训", "学习"]
                    travel_keywords = ["出差", "出行", "旅行", "外地", "拜访", "参观", "考察"]
                    holiday_keywords = ["假期", "休假", "休息", "放假", "请假"]
                    deadline_keywords = ["截止", "deadline", "交付", "提交", "结项", "验收", "审核", "检查"]
                    
                    if any(keyword in content for keyword in meeting_keywords):
                        result.event_type = "blue"  # 会议
                    elif any(keyword in content for keyword in travel_keywords):
                        result.event_type = "orange"  # 出差
                    elif any(keyword in content for keyword in holiday_keywords):
                        result.event_type = "green"  # 假期
                    elif any(keyword in content for keyword in deadline_keywords):
                        result.event_type = "red"  # 截止日期
                    else:
                        result.event_type = "blue"  # 默认为会议
                        
                return result
            
            return default_event
            
        except Exception as e:
            logger.error(f"Error in LLM processing or parsing: {str(e)}")
            return default_event
        
    except Exception as e:
        logger.error(f"Error detecting calendar event: {str(e)}")
        # 出错时返回默认值
        return CalendarEventInfo(
            title="",
            start_time="",
            end_time="",
            location=None,
            description=None,
            event_type="blue",
            is_detected=False
        )

def format_calendar_data(event_info):
    """将事件信息格式化为前端所需的JSON格式"""
    if not event_info or not event_info.is_detected:
        return None
        
    # 处理时间格式
    try:
        # 处理开始时间
        if event_info.start_time:
            # 尝试几种常见时间格式
            formats_to_try = [
                "%Y-%m-%d %H:%M",  # 标准格式 2023-06-15 14:00
                "%Y-%m-%d %H:%M:%S",  # 带秒的格式
                "%Y/%m/%d %H:%M",  # 斜杠分隔日期
                "%Y年%m月%d日 %H:%M",  # 中文格式
                "%Y年%m月%d日 %H点%M分",  # 另一种中文格式
                "%m/%d/%Y %H:%M",  # 美国格式
                "%Y-%m-%d",  # 仅日期格式
            ]
            
            start_time = None
            for fmt in formats_to_try:
                try:
                    start_time = datetime.strptime(event_info.start_time, fmt)
                    break
                except ValueError:
                    continue
            
            # 如果没有匹配到任何格式，使用默认值
            if not start_time:
                start_time = datetime.now() + timedelta(days=1)
                start_time = start_time.replace(hour=10, minute=0, second=0, microsecond=0)
        else:
            # 如果没有开始时间但检测到日程信息，默认设置为明天上午10点
            start_time = datetime.now() + timedelta(days=1)
            start_time = start_time.replace(hour=10, minute=0, second=0, microsecond=0)
        
        # 处理结束时间
        if event_info.end_time:
            # 尝试相同的格式列表
            end_time = None
            for fmt in formats_to_try:
                try:
                    end_time = datetime.strptime(event_info.end_time, fmt)
                    break
                except ValueError:
                    continue
                    
            # 如果没有匹配到任何格式，使用默认值
            if not end_time:
                end_time = start_time + timedelta(hours=1)
        else:
            # 如果没有结束时间，根据事件类型设置默认持续时间
            if event_info.event_type == "blue":  # 会议
                end_time = start_time + timedelta(hours=1)
            elif event_info.event_type == "orange":  # 出差
                end_time = start_time + timedelta(hours=8)  # 出差默认8小时
            elif event_info.event_type == "green":  # 假期
                # 假期可能是全天，设置到当天结束
                end_time = start_time.replace(hour=23, minute=59, second=59)
            elif event_info.event_type == "red":  # 截止日期
                end_time = start_time + timedelta(minutes=30)  # 截止时间默认30分钟
            else:  # 其他
                end_time = start_time + timedelta(hours=1)  # 默认1小时
        
        # 强制结束时间与开始时间在同一天
        if end_time.date() != start_time.date():
            # 如果跨天，将结束时间设为开始时间当天的最后一刻
            end_time = start_time.replace(hour=23, minute=59, second=59)

        # 如果结束时间早于或等于开始时间，则设置为开始时间后1小时
        if end_time <= start_time:
            # 如果调整后仍然不合法（例如开始时间是23:59），确保至少有1分钟的间隔
            if start_time.hour == 23 and start_time.minute == 59:
                 end_time = start_time # 如果无法增加，则保持一致
            else:
                 end_time = start_time + timedelta(hours=1)
                 # 再次检查，如果增加1小时后跨天，则设置到当天结束
                 if end_time.date() != start_time.date():
                     end_time = start_time.replace(hour=23, minute=59, second=59)

    except Exception as e:
        # 如果时间格式解析错误，使用默认时间
        logger.error(f"Error parsing time format: {str(e)}")
        start_time = datetime.now() + timedelta(days=1)
        start_time = start_time.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
    
    # 格式化为ISO格式
    start_iso = start_time.isoformat()
    end_iso = end_time.isoformat()
    
    return {
        "title": event_info.title,
        "start": start_iso,
        "end": end_iso,
        "location": event_info.location or "",
        "description": event_info.description or "",
        "type": event_info.event_type,
        "reminder": "30min",  # 默认提醒时间
    } 