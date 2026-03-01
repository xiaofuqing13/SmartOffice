"""Services for the AI app."""

import os
import yaml
import io
import base64
from django.conf import settings
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader, 
    TextLoader, 
    Docx2txtLoader, 
    CSVLoader,
    UnstructuredExcelLoader
)
from langchain.prompts import PromptTemplate
import tempfile
import json
from typing import List, Dict, Any, Optional
from .models import Document, DocumentChunk, AIChat, AIChatMessage, AIRecommendation
from apps.calendar.models import CalendarEvent
from django.utils import timezone
from datetime import timedelta
from langchain_core.runnables import RunnableSequence
import re
import subprocess
import threading
from PIL import Image

# 加载配置文件
def load_yaml_config():
    """从setting.yaml加载配置"""
    try:
        # 获取项目根目录
        base_dir = Path(settings.BASE_DIR)
        yaml_path = base_dir / "setting.yaml"
        
        if not yaml_path.exists():
            print(f"配置文件不存在: {yaml_path}")
            return {}
            
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config
    except Exception as e:
        print(f"加载配置文件出错: {e}")
        return {}

# 加载配置
yaml_config = load_yaml_config()
ai_config = yaml_config.get('ai', {})
            
# 配置OpenAI API
OPENAI_API_KEY = ai_config.get('openai_api_key', getattr(settings, 'OPENAI_API_KEY', None))
OPENAI_API_BASE = ai_config.get('openai_api_base', getattr(settings, 'OPENAI_API_BASE', None))
AI_MODEL = ai_config.get('model', getattr(settings, 'AI_MODEL', 'gpt-3.5-turbo'))

# 视觉模型配置
VISION_MODEL = ai_config.get('vision_model', 'gpt-4-vision-preview')
ENABLE_VISION_API = ai_config.get('enable_vision_api', False)
MAX_VISION_TOKENS = ai_config.get('max_vision_tokens', 1000)
VISION_API_TIMEOUT = ai_config.get('vision_api_timeout', 60)

if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    
if OPENAI_API_BASE:
    os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE

print(f"API配置 - 基础URL: {OPENAI_API_BASE}, 常规模型: {AI_MODEL}, 视觉模型: {VISION_MODEL}, 视觉API启用: {ENABLE_VISION_API}")

# 导入日历服务模块
from apps.calendar import nlp_service
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

class LangChainAssistant:
    """使用LangChain框架的AI助手服务类."""
    
    def __init__(self, user=None):
        """初始化LangChain助手."""
        self.user = user
        try:
            print(f"正在初始化LangChain助手...")
            print(f"使用API基础URL: {OPENAI_API_BASE}")
            print(f"使用AI模型: {AI_MODEL}")
            
            # 初始化LLM
            self.llm = ChatOpenAI(
                streaming=True,
                temperature=0.1,
                model_name=AI_MODEL,
                openai_api_key=OPENAI_API_KEY,
                openai_api_base=OPENAI_API_BASE,
                timeout=120  # 超时时间120秒
            )
            
            # 设置日历工具模块的全局用户
            nlp_service._user = user
            
            print(f"LangChain助手初始化成功")
        except Exception as e:
            print(f"初始化LangChain助手时出错: {e}")
            self.llm = None
    
    def set_user(self, user):
        """设置当前用户，以便工具可以使用"""
        self.user = user
        # 设置日历工具模块的全局用户
        nlp_service._user = user

    def get_tools(self):
        """获取可用的工具列表"""
        # 在这里可以添加更多的工具
        return [nlp_service.add_event, nlp_service.search_events, nlp_service.edit_event, nlp_service.delete_event, nlp_service.delete_events]

    def chat_with_tools_stream(self, messages: List[Dict[str, str]], document_ids: List[int] = None, ai_settings: Dict = None):
        """
        使用代理和工具进行流式聊天。
        根据代理是否使用工具，决定是流式输出文本，还是最后返回一个JSON对象。
        新增：
        - 如果提供了document_ids，则优先进行文档问答
        - 如果提供了ai_settings，则根据用户偏好调整AI回复风格
        """
        if not self.llm:
            yield "系统当前无法使用AI助手，请稍后再试。"
            return

        if self.user:
            self.set_user(self.user)
        else:
            yield json.dumps({"type": "error", "content": "错误：未设置当前用户，无法执行需要权限的操作。"})
            return

        user_input = messages[-1]['content']

        # --- 处理文档向量检索 ---
        if document_ids and len(document_ids) > 0:
            try:
                # 获取文档处理器
                processor = DocumentProcessor()
                
                # 获取相关文档块
                relevant_chunks = processor.search_relevant_chunks(
                    query=user_input,
                    limit=5,
                    document_ids=document_ids
                )
                
                if relevant_chunks:
                    # 构建文档上下文
                    doc_context = "\n\n".join([f"文档：{chunk['document_name']}，内容：{chunk['content']}" for chunk in relevant_chunks])
                    
                    # 准备增强后的用户消息
                    enhanced_message = f"""我基于用户上传的文档回答以下问题。
                    
文档内容：
{doc_context}

用户问题: {user_input}

请根据提供的文档内容，准确回答用户的问题。如果文档内容不足以回答问题，请明确指出。回答要简洁明了。"""
                    
                    # 直接使用普通聊天路径处理文档问答
                    system_prompt = """你是一个专业的文档助手，擅长分析文档并回答相关问题。请根据提供的文档内容回答用户问题。
如果文档内容不足以完全回答问题，请明确指出，不要编造信息。回答要简洁、专业。"""

                    chat_prompt = ChatPromptTemplate.from_messages([
                        ("system", system_prompt),
                        ("user", "{input}")
                    ])
                    
                    chain = chat_prompt | self.llm
                    for chunk in chain.stream({"input": enhanced_message}):
                        yield json.dumps({"type": "text_chunk", "content": chunk.content})
                    return
            except Exception as e:
                print(f"文档检索流程出错: {e}")
                # 如果文档检索失败，继续使用普通流程
        
        # --- 新增：直接命令处理 ---
        if user_input.startswith('__CMD_DELETE_EVENT_'):
            try:
                event_id = int(user_input.replace('__CMD_DELETE_EVENT_', ''))
                # 确保工具能访问到当前用户
                nlp_service._user = self.user
                result_message = nlp_service.delete_event.invoke({"event_id": event_id})
                yield json.dumps({
                    "type": "final_card",
                    "status": "success",
                    "content": result_message
                }, ensure_ascii=False)
            except Exception as e:
                yield json.dumps({
                    "type": "final_card",
                    "status": "error",
                    "content": f"执行删除命令时出错: {e}"
                }, ensure_ascii=False)
            return
        elif user_input.startswith('__CMD_DELETE_EVENTS_'):
            try:
                id_string = user_input.replace('__CMD_DELETE_EVENTS_', '')
                event_ids = [int(id_str) for id_str in id_string.split(',')]
                nlp_service._user = self.user
                result_message = nlp_service.delete_events.invoke({"event_ids": event_ids})
                yield json.dumps({
                    "type": "final_card", "status": "success", "content": result_message
                }, ensure_ascii=False)
            except Exception as e:
                yield json.dumps({
                    "type": "final_card", "status": "error", "content": f"执行批量删除时出错: {e}"
                }, ensure_ascii=False)
            return
        
        chat_history = []
        for msg in messages[:-1]:
            chat_history.append(HumanMessage(content=msg['content']) if msg['role'] == 'user' else AIMessage(content=msg['content']))

        # --- 现有路由功能：决定是普通聊天还是工具调用 ---
        tools = self.get_tools()
        tool_descriptions = "\n".join([f"- {tool.name}: {tool.description}" for tool in tools])
        
        router_prompt_template = f"""你是一个高效的路由分类器。根据用户的请求，判断该请求是应该由一个能够使用工具的AI代理来处理，还是一个普通的聊天机器人来回答。

可用的工具有:
{tool_descriptions}

用户的最新请求是: "{{user_input}}"

如果用户的请求明确需要使用上述任何一个工具（例如：安排会议、删除日程、查找事件），请只回答 "tool"。
如果用户的请求只是一个普通的问题、问候或对话，请只回答 "chat"。

你的回答只能是 "tool" 或 "chat" 这一个词，不能有任何其他内容。
"""
        
        router_prompt = PromptTemplate.from_template(router_prompt_template).format(user_input=user_input)
        
        # 为了路由判断，我们需要一个非流式的LLM实例
        non_streaming_llm = ChatOpenAI(
            streaming=False,
            temperature=0,
            model_name=AI_MODEL,
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_API_BASE,
            timeout=120
        )
        
        try:
            router_decision = non_streaming_llm.invoke(router_prompt).content.strip().lower()
            print(f"[AI Router] 路由决策: {router_decision}")
        except Exception as e:
            print(f"[AI Router] 路由决策失败: {e}，将默认进入聊天模式。")
            router_decision = "chat"

        # 2. 根据路由结果执行不同路径
        chat_history = []
        for msg in messages[:-1]:
            chat_history.append(HumanMessage(content=msg['content']) if msg['role'] == 'user' else AIMessage(content=msg['content']))

        if 'chat' in router_decision:
            # --- 普通聊天路径 (流式输出) ---
            print("[AI服务] 进入普通聊天路径。")
            try:
                # 构建系统提示，根据AI个性化设置调整
                system_prompt = "你是一个乐于助人的AI助手。"
                
                # 从ai_settings中获取个性化设置
                user_nickname = ""
                ai_tone = "professional"  # 默认风格
                ai_traits = ""
                ai_context = ""
                
                if ai_settings:
                    user_nickname = ai_settings.get('nickname', '')
                    ai_tone = ai_settings.get('tone', 'professional')
                    
                    # 处理自定义风格
                    if ai_tone == 'custom' and ai_settings.get('traits_text'):
                        ai_traits = ai_settings.get('traits_text', '')
                    
                    # 添加用户职位和其他信息到上下文
                    job_info = ai_settings.get('job', '')
                    other_info = ai_settings.get('other_info', '')
                    
                    if job_info:
                        ai_context += f"用户职位: {job_info}. "
                    
                    if other_info:
                        ai_context += f"用户提供的额外信息: {other_info}"
                
                # 添加称呼
                if user_nickname:
                    system_prompt += f" 请在回答中称呼用户为\"{user_nickname}\"。"
                
                # 添加风格指导
                if ai_tone == 'professional':
                    system_prompt += " 请使用专业严谨的语气回答，注重准确性和权威性。"
                elif ai_tone == 'friendly':
                    system_prompt += " 请使用亲切友好的语气回答，让用户感到温暖和舒适。可以适当使用礼貌的表情符号。"
                elif ai_tone == 'concise':
                    system_prompt += " 请使用简洁直接的语气回答，避免冗长，直奔主题。"
                elif ai_tone == 'custom' and ai_traits:
                    system_prompt += f" 请使用以下风格特点回答：{ai_traits}"
                
                # 添加用户上下文信息
                if ai_context:
                    system_prompt += f"\n\n用户背景信息：{ai_context}"
                
                chat_prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("user", "{input}"),
                ])
                chain = chat_prompt | self.llm
                for chunk in chain.stream({"input": user_input, "chat_history": chat_history}):
                    yield json.dumps({"type": "text_chunk", "content": chunk.content})
            except Exception as e:
                print(f"普通聊天流式处理出错: {e}")
                yield json.dumps({"type": "error", "content": f"抱歉，聊天时出现错误: {e}"})

        else:
            # --- 工具调用路径 (卡片式输出) ---
            print("[AI服务] 进入工具调用路径。")

            # 1. 立刻返回一个"处理中"的占位消息
            yield json.dumps({"type": "processing_start", "content": "正在为您处理日程..."}, ensure_ascii=False)

            prompt_template = f"""
你是一个智能办公助手，严格遵守以下规则。
当前日期和时间是 {timezone.now().strftime('%Y年%m月%d日 %H:%M')}。

核心指令:
1.  与用户交流时，直接回答。
2.  当用户的指令需要操作日历（如创建、查询、修改或删除日程）时，优先使用你拥有的工具来完成任务。

工具使用规则（极其重要）:
- **智能标题**: 创建事件时，你必须从用户的话中提取核心关键词作为标题，而不是使用整个句子。例如，对于"提醒我明天下午3点与市场部门开会讨论Q3预算"，标题应该是"与市场部门开会"或"Q3预算讨论会议"，而不是"提醒我明天下午3点与市场部门开会讨论Q3预算"。
- **搜索优先原则**: 在执行'edit_event'或'delete_event'之前，你**必须**拥有事件的ID。
  - 如果用户仅提供文本描述（如"删除预算会议"），使用 `query` 参数搜索。
  - **关键**: 如果用户的删除指令中提到了时间（如"删除明天所有日程"或"删除下午3点的会议"），你**必须**调用 `search_events` 工具，并将AI自己解析后的标准时间（如 '2025-07-10 15:00'）作为 `start_time` 参数传入进行搜索，即使没有其他文本关键词。
- **批量删除**: 如果 `search_events` 找到了多个日程，而用户意图是全部删除，请引导用户确认后，使用 `delete_events` 工具。
- **无ID操作**: 绝对不要在不知道事件ID的情况下调用'edit_event'或'delete_event'。
- **确认和完成**: 成功操作工具后，用一句清晰简洁的中文确认句告知用户。例如："好的，名为'团队会议'的事件已成功删除。"
- **智能创建**: 创建事件时，如果用户没有提供结束时间，你应该根据常识设置一个（例如，会议默认为1小时）。
- **时间解析**: 解析相对时间（如"明天下午2点"）时，你必须结合今天的日期。
"""

            # 添加个性化设置到提示中
            if ai_settings:
                user_nickname = ai_settings.get('nickname', '')
                ai_tone = ai_settings.get('tone', 'professional')
                
                # 处理自定义风格
                if ai_tone == 'custom' and ai_settings.get('traits_text'):
                    ai_traits = ai_settings.get('traits_text', '')
                else:
                    ai_traits = "" #确保ai_traits被定义
                
                # 添加用户职位和其他信息到上下文
                job_info = ai_settings.get('job', '')
                other_info = ai_settings.get('other_info', '')
                
                ai_context = ""
                if job_info:
                    ai_context += f"用户职位: {job_info}. "
                
                if other_info:
                    ai_context += f"用户提供的额外信息: {other_info}"

                if user_nickname:
                    prompt_template += f"\n请在回答中称呼用户为\"{user_nickname}\"。"
                
                # 添加风格指导
                if ai_tone == 'professional':
                    prompt_template += "\n请使用专业严谨的语气回答，注重准确性和权威性。"
                elif ai_tone == 'friendly':
                    prompt_template += "\n请使用亲切友好的语气回答，让用户感到温暖和舒适。"
                elif ai_tone == 'concise':
                    prompt_template += "\n请使用简洁直接的语气回答，避免冗长，直奔主题。"
                elif ai_tone == 'custom' and ai_traits:
                    prompt_template += f"\n请使用以下风格特点回答：{ai_traits}"
                
                # 添加用户上下文信息
                if ai_context:
                    prompt_template += f"\n\n用户背景信息：{ai_context}"

            prompt = ChatPromptTemplate.from_messages([
                ("system", prompt_template),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            agent = create_openai_tools_agent(self.llm, tools, prompt)
            # 返回中间步骤，以便我们分析工具调用
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, return_intermediate_steps=True, handle_parsing_errors=True)

            try:
                # 2. 在后台执行实际操作
                result = agent_executor.invoke({
                    "input": user_input,
                    "chat_history": chat_history,
                })
                
                final_output = result.get('output', '任务处理时出现未知问题。')
                intermediate_steps = result.get('intermediate_steps', [])

                # 新增：强制批量删除的后处理逻辑
                is_delete_intent = any(kw in user_input for kw in ['删除', '取消掉', '去掉', '清空'])
                if is_delete_intent and intermediate_steps:
                    last_action, last_tool_output = intermediate_steps[-1]
                    if last_action.tool == 'search_events' and isinstance(last_tool_output, dict):
                        found_events = last_tool_output.get('events', [])
                        if found_events:
                            event_ids = [event['id'] for event in found_events]
                            print(f"[AI服务] 搜索到 {len(event_ids)} 个事件，将强制执行批量删除。")
                            
                            # 强制调用批量删除工具
                            nlp_service._user = self.user # 确保用户身份
                            try:
                                # 使用invoke方法并传递正确的参数格式
                                delete_result = nlp_service.delete_events.invoke({"event_ids": event_ids})
                                print(f"[AI服务] 批量删除结果: {delete_result}")
                                
                                # 手动构建最终成功消息并返回
                                yield json.dumps({
                                    "type": "final_card",
                                    "status": "success",
                                    "content": delete_result
                                }, ensure_ascii=False)
                                return # 流程结束
                            except Exception as e:
                                print(f"[AI服务] 批量删除出错: {e}")
                                yield json.dumps({
                                    "type": "final_card",
                                    "status": "error",
                                    "content": f"删除日程时出现错误: {e}"
                                }, ensure_ascii=False)
                                return
                
                # --- 优化后的逻辑判断：确定操作状态 ---
                status = "clarification" # 默认为需要澄清
                
                # 检查是否有工具被实际执行
                if intermediate_steps:
                    # 检查最后一个被执行的工具
                    last_action = intermediate_steps[-1][0]
                    tool_name = last_action.tool
                    
                    # 定义哪些工具的调用意味着最终成功
                    successful_actions = ['add_event', 'edit_event', 'delete_event', 'delete_events']
                    
                    if tool_name in successful_actions:
                        # 假设如果这些工具被调用且没有在agent层面抛出异常，操作就是成功的
                        # 更严谨的判断可以基于工具的返回内容
                        tool_output = intermediate_steps[-1][1]
                        if "错误" not in str(tool_output) and "失败" not in str(tool_output):
                           status = "success"
                        else:
                           status = "error" # 工具返回了错误信息
                    else:
                        # 如果调用的是search_events等非终结性工具，则认为是澄清
                        status = "clarification"
                
                # 如果AI没有调用任何工具，只是返回了一段文本，那它就是在提问或澄清
                # 这种情况 status 保持默认的 "clarification" 即可

                print(f"[AI服务] 工具执行完毕. 状态: {status}, 最终消息: {final_output}")

                # 如果是创建成功，提取event_id并一起返回
                if status == "success" and tool_name == 'add_event':
                    tool_observation = intermediate_steps[-1][1]
                    
                    # 手动构建更友好的中文回复
                    event_data = tool_observation.get('event', {})
                    title = event_data.get('title', '未命名事件')
                    start_iso = event_data.get('start')
                    
                    if start_iso:
                        # 解析ISO格式时间并格式化为中文样式
                        from dateutil import parser
                        start_dt = parser.isoparse(start_iso)
                        time_str = start_dt.strftime('%Y年%m月%d日 %H:%M')
                        final_output = f"好的，名为\"{title}\"的事件已成功创建，时间为 {time_str}。"
                    else:
                        # Fallback
                        final_output = f"好的，名为\"{title}\"的事件已成功创建。"

                    match = re.search(r"ID为 (\d+)", str(tool_observation.get("message", "")))
                    if match:
                        event_id = int(match.group(1))
                        yield json.dumps({
                            "type": "final_card", 
                            "status": "success", 
                            "content": final_output, 
                            "event_id": event_id
                        }, ensure_ascii=False)
                    else:
                        # Fallback
                        yield json.dumps({"type": "final_card", "status": status, "content": final_output}, ensure_ascii=False)
                else:
                    yield json.dumps({"type": "final_card", "status": status, "content": final_output}, ensure_ascii=False)

            except Exception as e:
                print(f"代理执行出错: {e}")
                yield json.dumps({"type": "error", "status": "error", "content": f"抱歉，执行任务时出现错误: {e}"})

    def chat(self, user_message):
        """
        与LangChain助手交互.
        
        Args:
            user_message: 用户消息
            
        Returns:
            AI助手的回复
        """
        try:
            if not self.llm:
                print("LLM未初始化，尝试重新初始化...")
                self.__init__()
            if not self.llm:
                return "系统当前无法使用AI助手，请稍后再试。"
            # 限制输入长度
            if len(user_message) > 8000:
                user_message = user_message[:8000] + "...(内容已截断)"
            print(f"发送到LangChain的消息: {user_message[:100]}...")
            # 直接用llm.invoke
            response = self.llm.invoke(user_message)
            print(f"接收到LangChain的回复类型: {type(response)}")
            # 正确处理响应对象，获取其中的文本内容
            if hasattr(response, 'content'):
                # 处理ChatOpenAI返回的AIMessage对象
                content = response.content
            elif isinstance(response, str):
                # 如果直接返回字符串
                content = response
            elif isinstance(response, dict) and 'content' in response:
                # 如果返回字典格式
                content = response['content']
            else:
                # 兜底方案，尝试转换为字符串
                try:
                    content = str(response)
                    # 检查是否包含向量等不应该直接展示的内容
                    if '[' in content and ']' in content and any(c.isdigit() for c in content):
                        # 可能是向量数据，返回错误信息
                        content = "抱歉，AI生成结果格式错误。请联系管理员检查API配置。"
                except:
                    content = "抱歉，无法解析AI返回的内容。"
            
            print(f"处理后的回复内容: {content[:100]}...")
            return content
        except Exception as e:
            if 'timeout' in str(e).lower():
                return "AI生成超时，请简化需求或稍后重试。"
            print(f"与LangChain交互时出错: {e}")
            return "抱歉，AI生成失败，请稍后重试。"
    
    def chat_stream(self, user_message):
        """
        流式生成AI回复，每次yield一小段内容。
        """
        try:
            if not self.llm:
                self.__init__()
            if not self.llm:
                yield "系统当前无法使用AI助手，请稍后再试。"
                return
            # 限制输入长度
            if len(user_message) > 8000:
                user_message = user_message[:8000] + "...(内容已截断)"
            print(f"[stream] 发送到LangChain的消息: {user_message[:100]}...")
            # 直接用llm.stream
            for chunk in self.llm.stream(user_message):
                print(f"接收到流式回复块类型: {type(chunk)}")
                # 正确处理响应对象，获取其中的文本内容
                if hasattr(chunk, 'content'):
                    # 处理ChatOpenAI返回的AIMessageChunk对象
                    content = chunk.content
                elif isinstance(chunk, str):
                    # 直接是字符串
                    content = chunk
                elif isinstance(chunk, dict) and 'content' in chunk:
                    # 字典格式
                    content = chunk['content']
                else:
                    # 兜底处理
                    try:
                        content = str(chunk)
                        # 检查是否为向量数据
                        if '[' in content and ']' in content and any(c.isdigit() for c in content):
                            continue  # 跳过可能的向量数据
                    except:
                        content = ""
                
                if content:  # 只在有内容时yield
                    yield content
        except Exception as e:
            print(f"流式交互时出错: {e}")
            yield "抱歉，AI生成失败，请稍后重试。"
            
    def chat_with_memory(self, messages, context_docs=None):
        """
        使用ConversationChain维护对话历史状态，提供上下文感知能力
        
        Args:
            messages: 消息历史列表，格式为[{"role": "user", "content": "..."}, ...]
            context_docs: 可选的文档上下文列表，格式为[{"content": "...", "source": "..."}, ...]
            
        Returns:
            AI助手的回复
        """
        try:
            if not self.llm:
                self.__init__()
            if not self.llm:
                return "系统当前无法使用AI助手，请稍后再试。"
                
            # 初始化对话记忆
            memory = ConversationBufferMemory()
            
            # 构建模板，包含文档上下文（如果有）
            template = ""
            if context_docs:
                template += "你是一个智能助手，将根据以下文档内容帮助用户回答问题。\n\n"
                template += "参考文档内容：\n"
                
                has_valid_content = False
                for i, doc in enumerate(context_docs):
                    source = doc.get("source", f"文档{i+1}")
                    content = doc.get('content', '')
                    
                    # 过滤可能的坐标数据或纯数值行
                    if content:
                        # 安全检查：过滤掉可能是坐标/向量的数值行
                        filtered_lines = []
                        for line in content.split('\n'):
                            # 跳过只包含数字、点和空格的行 (可能是坐标)
                            if re.match(r'^[\d\.\s]+$', line.strip()):
                                continue
                            # 跳过向量格式的行 (如 [0.123, 0.456, ...])
                            if re.match(r'^\[[\d\.\s,]+\]$', line.strip()):
                                continue
                            filtered_lines.append(line)
                        
                        content = '\n'.join(filtered_lines)
                    
                    if content.strip():  # 确保过滤后还有内容
                        template += f"[{source}]: {content}\n\n"
                        has_valid_content = True
                
                if has_valid_content:
                    template += "请基于以上文档信息回答用户问题，如果文档中没有相关信息，请明确说明。\n\n"
                else:
                    # 如果过滤后没有有效内容，则使用通用模板
                    template = "你是一个智能助手，将帮助用户回答问题。\n\n"
            else:
                template += "你是一个智能助手，将帮助用户回答问题。\n\n"
            
            template += "{history}\n当前问题: {input}"
            prompt_template = PromptTemplate(input_variables=["history", "input"], template=template)
            
            # 创建对话链
            conversation = ConversationChain(
                llm=self.llm,
                memory=memory,
                prompt=prompt_template,
                verbose=True
            )
            
            # 将历史消息添加到内存中
            for i in range(0, len(messages)-1, 2):
                if i+1 < len(messages):
                    user_msg = messages[i].get("content", "")
                    ai_msg = messages[i+1].get("content", "")
                    memory.chat_memory.add_user_message(user_msg)
                    memory.chat_memory.add_ai_message(ai_msg)
            
            # 最后一条用户消息
            last_message = messages[-1].get("content", "") if messages and messages[-1].get("role") == "user" else ""
            
            # 如果没有最后一条用户消息，返回错误
            if not last_message:
                return "无法处理空消息"
                
            # 限制输入长度
            if len(last_message) > 4000:
                last_message = last_message[:4000] + "...(内容已截断)"
                
            # 运行对话链
            print(f"发送到ConversationChain的消息: {last_message[:100]}...")
            response = conversation.predict(input=last_message)
            print(f"接收到ConversationChain的回复: {response[:100]}...")
            
            return response
            
        except Exception as e:
            if 'timeout' in str(e).lower():
                return "AI生成超时，请简化需求或稍后重试。"
            print(f"与ConversationChain交互时出错: {e}")
            return "抱歉，AI生成失败，请稍后重试。"
    
    def chat_with_memory_stream(self, messages, context_docs=None):
        """
        流式返回使用上下文记忆的聊天结果
        
        Args:
            messages: 消息历史列表
            context_docs: 可选的文档上下文列表
        """
        try:
            if not self.llm:
                self.__init__()
            if not self.llm:
                yield "系统当前无法使用AI助手，请稍后再试。"
                return
                
            # 构建上下文模板
            context_content = ""
            if context_docs:
                context_content = "参考文档内容：\n"
                for i, doc in enumerate(context_docs):
                    source = doc.get("source", f"文档{i+1}")
                    content = doc.get('content', '')
                    
                    # 过滤可能的坐标数据或纯数值行
                    if content:
                        # 安全检查：过滤掉可能是坐标/向量的数值行
                        filtered_lines = []
                        for line in content.split('\n'):
                            # 跳过只包含数字、点和空格的行 (可能是坐标)
                            if re.match(r'^[\d\.\s]+$', line.strip()):
                                continue
                            # 跳过向量格式的行 (如 [0.123, 0.456, ...])
                            if re.match(r'^\[[\d\.\s,]+\]$', line.strip()):
                                continue
                            filtered_lines.append(line)
                        
                        content = '\n'.join(filtered_lines)
                    
                    if content.strip():  # 确保过滤后还有内容
                        context_content += f"[{source}]: {content}\n\n"
                
                if context_content.strip() == "参考文档内容：":
                    # 如果过滤后没有任何内容，则清空上下文
                    context_content = ""
                else:
                    context_content += "请基于以上文档信息回答用户问题，如果文档中没有相关信息，请明确说明。\n\n"
            
            # 优化：去除HTML标签，获取纯文本内容
            def remove_html(text):
                if not text:
                    return ""
                # 移除HTML标签
                clean_text = re.sub(r'<[^>]*>', '', text)
                # 处理HTML实体
                clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>')
                clean_text = clean_text.replace('&amp;', '&').replace('&quot;', '"')
                return clean_text
            
            # 构建历史对话内容
            history_content = ""
            for msg in messages:
                role = "用户" if msg.get("role") == "user" else "AI助手"
                # 清理HTML内容
                content = remove_html(msg.get('content', ''))
                # 对用户最后一条消息特殊处理
                if msg == messages[-1] and msg.get("role") == "user":
                    continue  # 最后一条用户消息将单独放入提示词
                else:
                    history_content += f"{role}: {content}\n\n"
            
            # 获取最后一条用户消息
            last_message = ""
            if messages and messages[-1].get("role") == "user":
                last_message = remove_html(messages[-1].get('content', ''))
            
            # 如果没有最后一条用户消息，返回错误
            if not last_message:
                yield "无法处理空消息"
                return
                
            # 限制输入长度
            if len(last_message) > 4000:
                last_message = last_message[:4000] + "...(内容已截断)"
            
            # 如果历史内容过长，截断
            if len(history_content) > 8000:
                history_content = "...(历史记录过长，已截断)\n\n" + history_content[-8000:]
            
            # 构建完整的提示词
            prompt = f"""你是一个智能助手，将基于上下文和历史对话帮助用户回答问题。

{context_content}

对话历史：
{history_content}

当前问题: {last_message}

请基于上下文和对话历史回答用户的当前问题。如果是文档相关问题，请尽量引用文档内容。回答要全面、准确、详细。
"""
            
            print(f"[stream] 发送到LangChain的消息: {prompt[:200]}...{prompt[-200:] if len(prompt) > 400 else ''}")
            
            # 流式返回结果
            for chunk in self.llm.stream(prompt):
                content = getattr(chunk, 'content', str(chunk))
                yield content
                
        except Exception as e:
            print(f"流式对话记忆交互时出错: {e}")
            yield "抱歉，AI生成失败，请稍后重试。"


class DocumentProcessor:
    """文档处理服务类，处理文件解析、分块和向量化"""
    
    # 支持的文件类型映射
    SUPPORTED_FILE_TYPES = {
        'pdf': ['application/pdf'],
        'txt': ['text/plain'],
        'doc': ['application/msword'],
        'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'md': ['text/markdown', 'text/x-markdown', 'text/plain', 'application/octet-stream'],
        'csv': ['text/csv', 'application/csv'],
        'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        'xls': ['application/vnd.ms-excel'],
        'jpg': ['image/jpeg'],
        'jpeg': ['image/jpeg'],
        'png': ['image/png'],
        'bmp': ['image/bmp'],
        'gif': ['image/gif'],
        'webp': ['image/webp'],
        'svg': ['image/svg+xml'],
        'tiff': ['image/tiff'],
    }
    
    def __init__(self):
        """初始化文档处理器"""
        try:
            # 初始化OpenAI嵌入模型（新版langchain_openai）
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-ada-002",
                openai_api_key=OPENAI_API_KEY,
                openai_api_base=OPENAI_API_BASE
            )
            
            # 初始化文本分割器
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
                length_function=len,
            )
            
            # 视觉模型仅用于图片文件，不用于PDF内的图像
            if ENABLE_VISION_API:
                self.vision_llm = ChatOpenAI(
                    model=VISION_MODEL,
                    temperature=0,
                    max_tokens=MAX_VISION_TOKENS,
                    openai_api_key=OPENAI_API_KEY,
                    openai_api_base=OPENAI_API_BASE,
                    timeout=VISION_API_TIMEOUT
                )
                print(f"视觉模型API初始化成功: {VISION_MODEL}, max_tokens={MAX_VISION_TOKENS} (仅用于图片文件)")
            else:
                self.vision_llm = None
                print("视觉模型API未启用")
                
        except Exception as e:
            print(f"初始化文档处理器时出错: {e}")
            self.embeddings = None
            self.text_splitter = None
            self.vision_llm = None

    def is_supported_file(self, file_obj) -> bool:
        """检查文件类型是否支持"""
        content_type = file_obj.content_type
        file_name = getattr(file_obj, 'name', '')
        file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
        
        print(f"[文件上传调试] 文件名: {file_name}, 内容类型: {content_type}, 扩展名: {file_ext}")
        
        # 如果是markdown文件但MIME类型不匹配，尝试根据文件扩展名判断
        if file_ext == 'md':
            print(f"[文件上传调试] 检测到Markdown文件，扩展名: {file_ext}")
            return True
            
        # 常规MIME类型检查
        for file_type, mimes in self.SUPPORTED_FILE_TYPES.items():
            if content_type in mimes:
                print(f"[文件上传调试] 文件类型匹配: {file_type}")
                return True
                
        print(f"[文件上传调试] 不支持的文件类型: {content_type}")
        return False
    
    def get_file_type(self, file_obj) -> str:
        """获取文件类型"""
        content_type = file_obj.content_type
        file_name = getattr(file_obj, 'name', '')
        file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
        
        # 如果是markdown文件但MIME类型不匹配，根据扩展名返回
        if file_ext == 'md':
            return 'md'
            
        # 常规文件类型判断
        for file_type, mimes in self.SUPPORTED_FILE_TYPES.items():
            if content_type in mimes:
                return file_type
        return "unknown"
    
    def process_document(self, document_id: int) -> bool:
        """处理文档，解析文本、分块并创建向量嵌入"""
        try:
            # 获取文档对象
            document = Document.objects.get(id=document_id)
            # 更新状态为处理中
            document.status = Document.DocumentStatus.PROCESSING
            document.save()
            # 解析文件内容
            raw_text = self._extract_text(document.file.path, document.file_type)
            # 针对图片类型，直接整体保存为一个chunk
            if document.file_type in ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp']:
                chunks = [raw_text] if raw_text.strip() else []
            else:
                chunks = self._split_text(raw_text)
            # 创建并保存文档块
            self._create_document_chunks(document, chunks)
            # 更新状态为完成
            document.status = Document.DocumentStatus.COMPLETED
            document.save()
            return True
        except Exception as e:
            print(f"处理文档时出错: {str(e)}")
            try:
                document = Document.objects.get(id=document_id)
                document.status = Document.DocumentStatus.FAILED
                document.error_message = str(e)
                document.save()
            except:
                pass
            return False
    
    def _extract_text_from_image(self, image_path: str) -> str:
        """使用视觉模型API从图像中提取文本"""
        if not ENABLE_VISION_API or not self.vision_llm:
            return "[未启用视觉API，无法识别图片]"
        
        try:
            # 获取文件扩展名以确定图像类型
            file_ext = os.path.splitext(image_path)[1].lower().strip('.')
            
            # 根据文件扩展名确定MIME类型
            mime_mapping = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'bmp': 'image/bmp',
                'webp': 'image/webp'
            }
            
            mime_type = mime_mapping.get(file_ext, 'image/jpeg')  # 默认为jpeg
            print(f"[视觉OCR] 图像类型: {file_ext}, MIME类型: {mime_type}")
            
            # 读取图像，确保转换为支持的格式
            img = Image.open(image_path)
            
            # 将图像转换为RGB模式（去除透明通道）
            if img.mode == 'RGBA':
                # PNG图像可能有透明通道，需要转换
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # 3是alpha通道
                img = background
            elif img.mode not in ['RGB', 'L']:
                # 其他非标准模式转换为RGB
                img = img.convert('RGB')
                
            # 转换为JPEG或PNG
            img_byte_arr = io.BytesIO()
            save_format = 'JPEG' if mime_type == 'image/jpeg' else file_ext.upper()
            
            # 确保格式是PIL支持的
            if save_format not in ['JPEG', 'PNG', 'GIF', 'BMP', 'WEBP']:
                save_format = 'JPEG'
                mime_type = 'image/jpeg'
            
            img.save(img_byte_arr, format=save_format)
            img_byte_arr.seek(0)
            image_data = img_byte_arr.read()
            
            # 编码为base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # 构建消息
            messages = [
                SystemMessage(content="你是一个图像OCR助手。请从图像中提取所有可见的文本内容，只返回文本内容，不要添加任何解释或描述。"),
                HumanMessage(content=[
                    {"type": "text", "text": "请从这个图像中提取所有文本内容:"},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                ])
            ]
            
            # 调用视觉模型API
            print(f"[视觉OCR] 处理图像: {image_path}")
            response = self.vision_llm.invoke(messages)
            extracted_text = response.content
            
            # 过滤掉可能的响应修饰词
            cleaned_text = re.sub(r'^(以下是|这是|图像中的|文本内容为：|文本内容是：|提取的文本是：)', '', extracted_text)
            cleaned_text = cleaned_text.strip()
            
            print(f"[视觉OCR] 提取文本成功，长度: {len(cleaned_text)} 字符")
            return cleaned_text
        except Exception as e:
            print(f"[视觉OCR] 图像处理出错: {e}")
            return f"[图像处理错误: {e}]"

    def _extract_text(self, file_path: str, file_type: str) -> str:
        """从文件中提取文本内容"""
        def _ensure_str(content):
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                return '\n'.join([_ensure_str(x) for x in content])
            elif content is None:
                return ''
            else:
                return str(content)
        try:
            if file_type == 'pdf':
                # 使用知识库模块的PDF文本提取方法
                try:
                    import pypdf
                    text = ""
                    with open(file_path, 'rb') as file:
                        pdf = pypdf.PdfReader(file)
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n\n"
                    return text
                except Exception as e:
                    print(f"PDF文本提取失败: {e}")
                    return f"文件处理错误: {e}"
            elif file_type == 'md':
                # 专门处理Markdown文件，使用多种方法尝试读取
                try:
                    # 尝试方法1：直接打开文件读取
                    print(f"[MD文件处理] 尝试直接读取文件: {file_path}")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return content
                except Exception as e1:
                    print(f"[MD文件处理] 直接读取失败: {e1}")
                    try:
                        # 尝试方法2：使用不同编码
                        print("[MD文件处理] 尝试使用其他编码")
                        encodings = ['utf-8-sig', 'gbk', 'latin1']
                        for encoding in encodings:
                            try:
                                with open(file_path, 'r', encoding=encoding) as f:
                                    content = f.read()
                                print(f"[MD文件处理] 使用 {encoding} 编码成功")
                                return content
                            except:
                                continue
                        
                        # 尝试方法3：二进制读取
                        print("[MD文件处理] 尝试二进制读取")
                        with open(file_path, 'rb') as f:
                            binary_content = f.read()
                            # 尝试多种编码解析
                            for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'latin1']:
                                try:
                                    content = binary_content.decode(encoding)
                                    print(f"[MD文件处理] 二进制读取并解码为 {encoding} 成功")
                                    return content
                                except:
                                    continue
                        
                        # 如果依然失败，返回错误信息
                        return "[无法解析Markdown文件内容]"
                    except Exception as e2:
                        print(f"[MD文件处理] 所有尝试均失败: {e2}")
                        return f"[Markdown文件读取错误: {str(e2)}]"
            elif file_type == 'txt':
                # txt文件也增加健壮的读取处理
                try:
                    # 尝试使用TextLoader
                    loader = TextLoader(file_path)
                    documents = loader.load()
                    return _ensure_str(documents[0].page_content)
                except Exception as e:
                    print(f"[TXT文件处理] TextLoader失败: {e}，尝试直接读取")
                    try:
                        # 直接读取尝试
                        with open(file_path, 'r', encoding='utf-8') as f:
                            return f.read()
                    except UnicodeDecodeError:
                        # 编码问题，尝试其他编码
                        for encoding in ['utf-8-sig', 'gbk', 'latin1']:
                            try:
                                with open(file_path, 'r', encoding=encoding) as f:
                                    return f.read()
                            except:
                                continue
                        return f"[TXT文件读取错误: 编码不支持]"
                    except Exception as e2:
                        return f"[TXT文件读取错误: {str(e2)}]"
            elif file_type == 'docx':
                loader = Docx2txtLoader(file_path)
                documents = loader.load()
                return _ensure_str(documents[0].page_content)
            elif file_type == 'doc':
                # doc文件也使用Docx2txtLoader尝试加载，不支持则提示
                try:
                    loader = Docx2txtLoader(file_path)  # 尝试用docx加载器
                    documents = loader.load()
                    return _ensure_str(documents[0].page_content)
                except Exception as e:
                    return f"[无法直接提取doc文件内容: {str(e)}]"
            elif file_type == 'csv':
                try:
                    # 尝试使用CSVLoader
                    print(f"[CSV文件处理] 尝试使用CSVLoader加载: {file_path}")
                    loader = CSVLoader(file_path)
                    documents = loader.load()
                    return _ensure_str("\n".join([doc.page_content for doc in documents]))
                except Exception as e:
                    print(f"[CSV文件处理] CSVLoader失败: {e}，尝试直接读取")
                    try:
                        # 直接读取尝试
                        import csv
                        csv_content = []
                        # 尝试不同的编码打开文件
                        for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'latin1']:
                            try:
                                with open(file_path, 'r', newline='', encoding=encoding) as f:
                                    reader = csv.reader(f)
                                    for row in reader:
                                        csv_content.append(", ".join(row))
                                print(f"[CSV文件处理] 使用 {encoding} 编码成功")
                                return "\n".join(csv_content)
                            except UnicodeDecodeError:
                                continue
                            except Exception as e2:
                                print(f"[CSV文件处理] CSV读取错误: {e2}")
                        
                        # 如果所有编码都失败，尝试以二进制方式读取
                        print("[CSV文件处理] 尝试二进制读取")
                        with open(file_path, 'rb') as f:
                            binary_content = f.read()
                            # 尝试检测编码并解析
                            for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'latin1']:
                                try:
                                    text_content = binary_content.decode(encoding)
                                    lines = text_content.split('\n')
                                    parsed_lines = []
                                    for line in lines:
                                        if line.strip():  # 非空行
                                            parsed_lines.append(line)
                                    print(f"[CSV文件处理] 二进制读取并解码为 {encoding} 成功")
                                    return "\n".join(parsed_lines)
                                except:
                                    continue
                        
                        return "[无法解析CSV文件内容，请检查文件格式和编码]"
                    except Exception as e3:
                        print(f"[CSV文件处理] 所有尝试均失败: {e3}")
                        return f"[CSV文件读取错误: {str(e3)}]"
            elif file_type in ['xlsx', 'xls']:
                try:
                    # 尝试使用UnstructuredExcelLoader
                    print(f"[Excel文件处理] 尝试使用UnstructuredExcelLoader加载: {file_path}")
                    loader = UnstructuredExcelLoader(file_path)
                    documents = loader.load()
                    return _ensure_str("\n".join([doc.page_content for doc in documents]))
                except Exception as e:
                    print(f"[Excel文件处理] UnstructuredExcelLoader失败: {e}，尝试使用pandas")
                    try:
                        # 尝试使用pandas读取
                        import pandas as pd
                        if file_type == 'xlsx':
                            df = pd.read_excel(file_path, engine='openpyxl')
                        else:  # xls
                            df = pd.read_excel(file_path, engine='xlrd')
                        
                        # 将DataFrame转换为易读的文本格式
                        excel_content = []
                        # 添加列名
                        excel_content.append(", ".join(str(col) for col in df.columns))
                        # 添加数据行
                        for _, row in df.iterrows():
                            excel_content.append(", ".join(str(cell) for cell in row))
                        
                        print("[Excel文件处理] pandas读取成功")
                        return "\n".join(excel_content)
                    except Exception as e2:
                        print(f"[Excel文件处理] pandas读取失败: {e2}，尝试读取文件头部")
                        # 如果pandas也失败，至少返回一些内容表示文件存在
                        return f"[Excel文件: {os.path.basename(file_path)}] (无法完全解析内容，但文件已成功上传)"
            elif file_type in ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp', 'svg', 'tiff']:  # 图片文件
                # SVG文件是矢量图，不适合OCR
                if file_type == 'svg':
                    return '[SVG矢量图，包含矢量图形数据]'
                
                # 使用视觉API进行OCR
                if ENABLE_VISION_API and self.vision_llm:
                    return self._extract_text_from_image(file_path)
                else:
                    return '[未启用视觉API，无法识别图片]'
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
        except Exception as e:
            print(f"提取文本内容时出错: {str(e)}")
            raise
    
    def _split_text(self, text: str) -> List[str]:
        """将文本分割成块"""
        if not self.text_splitter:
            raise ValueError("文本分割器未初始化")
            
        chunks = self.text_splitter.split_text(text)
        return chunks
    
    def _create_document_chunks(self, document: Document, chunks: List[str]):
        """创建并保存文档块，并添加向量嵌入"""
        # 首先删除现有的块
        DocumentChunk.objects.filter(document=document).delete()
        
        # 为每个文本块创建记录
        for i, chunk_text in enumerate(chunks):
            # 创建嵌入向量
            embedding = None
            if self.embeddings:
                try:
                    embedding_vector = self.embeddings.embed_query(chunk_text)
                    embedding = json.dumps(embedding_vector)
                except Exception as e:
                    print(f"创建嵌入向量时出错: {str(e)}")
            
            # 创建文档块
            DocumentChunk.objects.create(
                document=document,
                content=chunk_text,
                chunk_index=i,
                embedding=embedding
            )
    
    def search_relevant_chunks(self, query: str, limit: int = 5, document_ids: List[int] = None) -> List[Dict[str, Any]]:
        """搜索与查询相关的文档块，可指定文档ID范围"""
        if not self.embeddings:
            raise ValueError("嵌入模型未初始化")
        try:
            query_embedding = self.embeddings.embed_query(query)
            if document_ids:
                print(f"[文档检索] 仅检索文档ID: {document_ids}")
                chunks = DocumentChunk.objects.filter(document_id__in=document_ids)
            else:
                print("[文档检索] 检索所有文档块")
                chunks = DocumentChunk.objects.all()
            results = []
            for chunk in chunks:
                if not chunk.embedding:
                    continue
                chunk_embedding = json.loads(chunk.embedding)
                similarity = self._calculate_cosine_similarity(query_embedding, chunk_embedding)
                results.append({
                    'chunk_id': chunk.id,
                    'document_id': chunk.document.id,
                    'content': chunk.content,
                    'similarity': similarity,
                    'document_name': chunk.document.original_filename
                })
            print(f"[文档检索] 共检索到{len(results)}个相关分块，前3条：")
            for r in results[:3]:
                print(f"  文档ID: {r['document_id']}，相似度: {r['similarity']:.4f}，内容片段: {r['content'][:30]}")
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]
        except Exception as e:
            print(f"搜索相关文档块时出错: {str(e)}")
            return []
    
    def _calculate_cosine_similarity(self, vec1, vec2) -> float:
        """计算两个向量之间的余弦相似度"""
        import numpy as np
        
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        similarity = dot_product / (norm_vec1 * norm_vec2)
        return float(similarity) 

# 添加获取消息内容的辅助函数
def _get_message_content(message):
    """从各种可能的消息对象中提取文本内容"""
    if isinstance(message, str):
        return message
    if hasattr(message, "content"):
        return message.content
    return ""

def run_graphrag_query_stream(query: str, method: str = "local", company_id: int = None):
    """
    使用流式输出运行GraphRAG查询。

    Args:
        query: 用户的查询字符串。
        method: GraphRAG的查询方法 ('local' 或 'basic')。
        company_id: 公司ID，用于加载特定于公司的配置。

    Yields:
        str: 查询过程中的输出块。
    """
    graphrag_path = os.path.abspath(os.path.join(settings.BASE_DIR, 'graphrag-main'))
    if not os.path.exists(graphrag_path):
        yield "GraphRAG路径未找到。"
        return

    if not company_id:
        yield "错误：未提供公司ID，无法定位知识库。"
        return

    # 构建特定于公司的配置文件路径
    config_file = f"ragtest/company_{company_id}_config.yaml"
    config_path = os.path.join(graphrag_path, config_file)

    if not os.path.exists(config_path):
        yield f"错误：未找到公司 {company_id} 的知识库配置文件：{config_file}"
        return

    # 构建命令
    command = [
        "python", "-m", "graphrag", "query",
        "--config", config_file,
        "--method", method,
        "--streaming",
        "--query", query
    ]

    # 获取当前环境变量并设置子进程的IO编码
    process_env = os.environ.copy()
    process_env["PYTHONIOENCODING"] = "utf-8"

    process = subprocess.Popen(
        command,
        cwd=graphrag_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='replace',
        bufsize=1,
        env=process_env
    )
    
    # --- 新增日志线程 ---
    def log_stderr(pipe):
        """读取并打印日志流"""
        for line in iter(pipe.readline, ''):
            print(f"[GraphRAG Log] {line.strip()}")
        pipe.close()

    stderr_thread = threading.Thread(target=log_stderr, args=(process.stderr,))
    stderr_thread.start()
    # ---------------------

    # 流式读取标准输出
    in_json_log_block = False
    brace_level = 0
    for line in iter(process.stdout.readline, ''):
        # 如果我们正处于要跳过的JSON日志块中
        if in_json_log_block:
            brace_level += line.count('{')
            brace_level -= line.count('}')
            # 如果括号闭合，说明JSON块结束
            if brace_level <= 0:
                in_json_log_block = False
            # 跳过当前行
            continue
        
        # 检测并开始跳过特定的JSON日志块
        if "INFO: Vector Store Args" in line:
            in_json_log_block = True
            brace_level = line.count('{') - line.count('}')
            # 处理整个JSON块在同一行的情况
            if brace_level <= 0:
                in_json_log_block = False
            continue

        # 移除 [Data: Sources (X)] 和多余的空格
        cleaned_line = re.sub(r'\[Data: Sources \(\d+\)\]', '', line).strip()
        
        # 如果代码执行到这里，说明不是要过滤的日志，可以发送到前端，但要确保非空
        if cleaned_line:
            yield cleaned_line + "\n" # 加回换行符，以便前端正确处理

    process.stdout.close()
    return_code = process.wait()

    # 等待日志线程结束
    stderr_thread.join()

    if return_code != 0:
        print(f"GraphRAG process exited with code {return_code}")
        # 不再通过yield返回错误，因为日志线程已经打印了错误
    
    process.stderr.close() 

def check_and_generate_reminders(user, event_instance=None):
    """
    检查并为指定用户生成日程提醒。
    可以针对单个日程实例，也可以检查所有未来日程。
    """
    now = timezone.now()
    print(f"[AI提醒服务] 开始为用户 '{user.username}' 检查提醒, 时间: {now}")

    # 定义提醒提前量映射
    reminder_delta = {
        '10min': timedelta(minutes=10),
        '30min': timedelta(minutes=30),
        '1hour': timedelta(hours=1),
        '1day': timedelta(days=1),
    }

    # 如果指定了单个日程，则只检查该日程
    if event_instance:
        events_to_check = [event_instance]
        print(f"[AI提醒服务] 检查单个日程: '{event_instance.title}' (ID: {event_instance.id})")
    else:
        # 否则，获取未来24小时内所有需要提醒的日程
        time_horizon = now + timedelta(days=1)
        events_to_check = CalendarEvent.objects.filter(
            participants=user,
            start__gte=now,
            start__lte=time_horizon
        ).exclude(reminder='none').order_by('start')
        print(f"[AI提醒服务] 检查时间范围: {now} to {time_horizon}, 找到 {events_to_check.count()} 个可能需要提醒的日程")
    
    # 只推送当前时间在提醒区间内的日程
    valid_events = []
    for evt in events_to_check:
        delta = reminder_delta.get(evt.reminder)
        if not delta:
            continue
        remind_time = evt.start - delta
        # 当前时间在提醒区间内（>=提醒时间，<开始时间）
        if remind_time <= now < evt.start:
            valid_events.append(evt)
    
    print(f"[AI提醒服务] 实际需要推送的日程数量: {len(valid_events)}")
    if not valid_events:
        return []

    reminders = []
    for event in valid_events:
        print(f"[AI提醒服务] 处理日程: {event.title}, ID: {event.id}, 开始时间: {event.start}, 提醒类型: {event.reminder}")
        try:
            # 检查AIRecommendation表中是否已有该日程的提醒记录
            existing_rec = AIRecommendation.objects.filter(user=user, type='calendar', reference_id=event.id).first()
            
            if existing_rec and existing_rec.is_read:
                # 如果已经存在已读的提醒记录，跳过不再生成新提醒
                print(f"[AI提醒服务] 该日程已有已读提醒记录，跳过: ID={existing_rec.id}")
                continue
            elif existing_rec and not existing_rec.is_read:
                # 如果存在未读的提醒记录，直接使用
                print(f"[AI提醒服务] 已存在未读的提醒记录: ID={existing_rec.id}")
                rec = existing_rec
                content = rec.content
            else:
                # 如果不存在任何提醒记录，创建新的
                # 生成AI提醒内容
                context = f"标题：{event.title}\n截止时间：{event.end.strftime('%Y-%m-%d %H:%M')}\n地点：{event.location or '无'}\n描述：{event.description or '无'}"
                prompt = f"请用简洁友好的语气，提醒我即将到来的日程，并简要说明事项。"
                ai = LangChainAssistant()
                content = ai.chat(f"{prompt}\n{context}")
                print(f"[AI提醒服务] 生成内容: {content[:50]}...")

                # 创建新的提醒记录
                rec = AIRecommendation.objects.create(
                    user=user,
                    type='calendar',
                    reference_id=event.id,
                    content=content,
                    is_read=False
                )
                print(f"[AI提醒服务] 创建新提醒记录: ID={rec.id}")
            
            reminders.append({
                'event_id': event.id,
                'title': event.title,
                'reminder': event.reminder,
                'ai_content': content,
                'recommendation_id': rec.id
            })
        except Exception as e:
            print(f"[AI提醒服务] 处理单个日程时出错: {str(e)}")
            # 继续处理下一个日程，不中断整个流程

    print(f"[AI提醒服务] 成功生成 {len(reminders)} 条提醒。")
    return reminders