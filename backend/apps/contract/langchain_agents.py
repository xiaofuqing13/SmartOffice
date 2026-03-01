"""
LangChain合同润色和检查代理
包括：
1. 语法和格式检测
2. 专业术语检测
3. 合同检查与风险分析
4. 法规查询
"""

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_community.cache import InMemoryCache
from langchain.globals import set_llm_cache
from django.conf import settings
from django.core.cache import cache as django_cache
import os
import sys
import json
import logging
import time
import re
import html
from langchain_core.runnables import RunnableSequence
from .models import Contract, ContractAction

# 配置日志
logger = logging.getLogger(__name__)

# 为日志处理程序设置UTF-8编码（解决Windows控制台GBK编码问题）
for handler in logger.handlers:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stderr:
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s', '%H:%M:%S'))
        handler.stream.reconfigure(encoding='utf-8', errors='backslashreplace')

# 设置LangChain内存缓存
set_llm_cache(InMemoryCache())

# 获取setting.yaml中的AI配置
OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_API_BASE = settings.OPENAI_API_BASE
AI_MODEL = settings.AI_MODEL

# 记录使用的配置
logger.info(f"使用AI接口基础URL: {OPENAI_API_BASE}")
logger.info(f"使用AI模型: {AI_MODEL}")

# 初始化LLM
llm = ChatOpenAI(
    temperature=0.1,
    model_name=AI_MODEL,  # 使用配置文件中指定的模型
    openai_api_key=OPENAI_API_KEY,
    openai_api_base=OPENAI_API_BASE
)

# 添加缓存键前缀
CACHE_KEY_PREFIX = "contract_polish_"
CACHE_TIMEOUT = 60 * 60  # 1小时

# 语法和格式检测代理
grammar_format_template = """你是一位专业的合同审核专家，专注于语法和格式问题。

请识别并改进以下合同文本中的问题：
1. 标点符号错误
2. 语法结构不当
3. 语句不通顺
4. 指代不明确
5. 格式不规范
6. 结构混乱

合同基本信息：
标题: {title}
类型: {contract_type}
签约对方: {company}
合同金额: {amount}

合同内容：
{content}

请找出5-10个明显的问题。对于每个问题，说明原文本、建议修改的文本和修改原因。

请严格按照以下JSON格式输出，不要有任何前言或说明：
[
  {{
    "original": "原文本",
    "suggested": "建议修改文本",
    "explanation": "修改原因"
  }}
]

如果没有问题，返回空数组 []。
"""

# 函数：清理和解析JSON响应
def clean_and_parse_json(json_str):
    """清理并解析JSON字符串，处理各种异常格式"""
    # 不记录完整JSON字符串，避免编码问题
    logger.debug(f"收到API响应，长度: {len(json_str) if json_str else 0}")
    
    if not json_str or json_str.strip() == '':
        logger.warning("收到空的JSON字符串")
        return []
        
    # 去除markdown代码块标记
    json_str = re.sub(r'```json\s*', '', json_str)
    json_str = re.sub(r'```\s*', '', json_str)
    
    try:
        # 首先尝试直接解析
        result = json.loads(json_str)
        logger.debug(f"成功解析JSON，包含 {len(result) if isinstance(result, list) else 1} 项结果")
        return result
    except json.JSONDecodeError:
        logger.warning(f"直接解析JSON失败，尝试清理和提取")
        # 如果直接解析失败，尝试提取JSON部分
        try:
            # 尝试找到第一个'['和最后一个']'之间的内容
            start_idx = json_str.find('[')
            end_idx = json_str.rfind(']')
            
            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                json_array = json_str[start_idx:end_idx+1]
                logger.debug(f"提取JSON数组，从位置 {start_idx} 到 {end_idx}")
                result = json.loads(json_array)
                logger.debug(f"成功解析提取的JSON数组，包含 {len(result)} 项")
                return result
            
            # 使用正则表达式提取JSON数组
            match = re.search(r'\[\s*\{.*\}\s*\]', json_str, re.DOTALL)
            if match:
                json_array = match.group(0)
                logger.debug(f"通过正则表达式提取JSON数组")
                result = json.loads(json_array)
                logger.debug(f"成功解析正则提取的JSON数组，包含 {len(result)} 项")
                return result
            
            # 尝试修复常见错误
            # 替换单引号为双引号
            fixed_str = json_str.replace("'", '"')
            # 修复缺少逗号的问题
            fixed_str = re.sub(r'}\s*{', '},{', fixed_str)
            # 确保有效的JSON数组
            if not fixed_str.strip().startswith('['):
                fixed_str = '[' + fixed_str
            if not fixed_str.strip().endswith(']'):
                fixed_str = fixed_str + ']'
                
            logger.debug(f"尝试修复JSON格式后解析")
            result = json.loads(fixed_str)
            logger.debug(f"修复后成功解析，包含 {len(result)} 项")
            return result
            
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            logger.error(f"无法解析JSON: {str(e)}")
            # 尝试最后的手段：手动提取部分数据
            try:
                # 查找所有可能的键值对
                pairs = re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', json_str)
                if pairs:
                    logger.debug(f"手动提取到 {len(pairs)} 对键值对")
                    # 创建一个简单的单项结果
                    return [{"original": "无法完全解析", "suggested": "请手动检查", "explanation": "AI响应格式有误"}]
            except Exception:
                pass
            
            # 返回空列表作为默认值
            return []

grammar_format_prompt = PromptTemplate(
    input_variables=["title", "contract_type", "company", "amount", "content"],
    template=grammar_format_template
)

# 使用|运算符替代LLMChain，创建RunnableSequence
grammar_chain = grammar_format_prompt | llm

# 专业术语检测代理
terminology_template = """你是一位专业的合同术语专家，专注于专业术语使用问题。

请识别并改进以下合同文本中的问题：
1. 非正式或不专业的表述
2. 行业术语使用不当
3. 法律术语使用不准确
4. 模糊不清的条款用语
5. 可能导致歧义的表述

合同基本信息：
标题: {title}
类型: {contract_type}
签约对方: {company}
合同金额: {amount}

注意：这是一份"{contract_type}"类型的合同，请特别注意该类合同常用的专业术语。

合同内容：
{content}

请找出3-8个明显的术语问题。对于每个问题，说明原文本、建议修改的文本和修改原因。

请严格按照以下JSON格式输出，不要有任何前言或说明：
[
  {{
    "original": "原文本",
    "suggested": "建议修改文本",
    "explanation": "修改原因"
  }}
]

如果没有问题，返回空数组 []。
"""

terminology_prompt = PromptTemplate(
    input_variables=["title", "contract_type", "company", "amount", "content"],
    template=terminology_template
)

# 使用|运算符替代LLMChain
terminology_chain = terminology_prompt | llm

# 合同检查代理 - 法律合规性检查
legal_compliance_template = """你是一位法律专家，专注于合同的法律合规性问题。

请识别以下合同中可能存在的法律问题：
1. 违反法律法规的条款
2. 可能被认为无效或者效力待定的条款
3. 权利义务不对等的条款
4. 免责条款是否合法
5. 违约责任是否明确且合法

合同基本信息：
标题: {title}
类型: {contract_type}
签约对方: {company}
合同金额: {amount}

合同内容：
{content}

请找出2-5个明显的法律合规性问题。

请严格按照以下JSON格式输出，不要有任何前言或说明：
[
  {{
    "title": "问题标题",
    "current": "当前条款内容",
    "problem": "问题描述"
  }}
]

如果没有发现问题，返回空数组 []。
"""

legal_compliance_prompt = PromptTemplate(
    input_variables=["title", "contract_type", "company", "amount", "content"],
    template=legal_compliance_template
)

# 使用|运算符替代LLMChain
legal_compliance_chain = legal_compliance_prompt | llm

# 合同检查代理 - 条款完整性检查
completeness_template = """你是一位合同专家，专注于合同条款的完整性。

请检查合同是否缺少重要条款：
1. 缺少必要的权利义务条款
2. 缺少争议解决条款
3. 缺少合同终止条款
4. 缺少保密条款（如适用）
5. 缺少不可抗力条款
6. 缺少其他根据合同类型应当具备的特殊条款

合同基本信息：
标题: {title}
类型: {contract_type}
签约对方: {company}
合同金额: {amount}

注意：这是一份"{contract_type}"类型的合同，请特别注意该类合同应具备的特定条款。

合同内容：
{content}

请找出1-3个明显缺失的条款。

请严格按照以下JSON格式输出，不要有任何前言或说明：
[
  {{
    "title": "问题标题",
    "suggestion": "建议添加的内容"
  }}
]

如果没有发现问题，返回空数组 []。
"""

completeness_prompt = PromptTemplate(
    input_variables=["title", "contract_type", "company", "amount", "content"],
    template=completeness_template
)

# 使用|运算符替代LLMChain
completeness_chain = completeness_prompt | llm

# 合同检查代理 - 风险提示
risk_alert_template = """你是一位风险管理专家，专注于识别合同中的潜在风险。

请识别以下类型的风险：
1. 商业风险
2. 履约风险
3. 付款风险
4. 知识产权风险
5. 责任风险
6. 声誉风险

合同基本信息：
标题: {title}
类型: {contract_type}
签约对方: {company}
合同金额: {amount}

合同内容：
{content}

请找出2-3个最值得关注的风险并给出建议。

请严格按照以下JSON格式输出，不要有任何前言或说明：
[
  {{
    "title": "风险标题",
    "suggestion": "风险管理建议"
  }}
]

如果没有发现明显风险，返回空数组 []。
"""

risk_alert_prompt = PromptTemplate(
    input_variables=["title", "contract_type", "company", "amount", "content"],
    template=risk_alert_template
)

# 使用|运算符替代LLMChain
risk_alert_chain = risk_alert_prompt | llm

# 法规查询模板
regulation_query_template = """你是一位专业的法律顾问，精通中国合同法和相关法律法规。

请针对以下合同问题，提供相关的法律法规依据和专业建议：

问题标题: {issue_title}
问题内容: {issue_content}
问题描述: {issue_problem}
合同类型: {contract_type}

请提供以下信息：
1. 与此问题最相关的法律法规名称（如《中华人民共和国合同法》、《中华人民共和国民法典》等）
2. 相关法条的具体内容和解释
3. 针对此问题的专业修改建议

请以JSON格式回复，不要有任何前言或说明：
{{
  "regulation": "相关法律法规名称",
  "regulation_content": "相关法条内容和解释",
  "suggestion": "专业修改建议"
}}
"""

regulation_query_prompt = PromptTemplate(
    input_variables=["issue_title", "issue_content", "issue_problem", "contract_type"],
    template=regulation_query_template
)

regulation_query_chain = regulation_query_prompt | llm

# 添加获取消息内容的辅助函数
def _get_message_content(message):
    """从各种可能的消息对象中提取文本内容"""
    if hasattr(message, 'content'):
        # AIMessage对象
        return message.content
    elif isinstance(message, dict) and 'content' in message:
        # 字典形式的消息
        return message['content']
    elif isinstance(message, str):
        # 已经是字符串
        return message
    else:
        # 其他情况，尝试字符串转换
        return str(message)

# 合同润色助手
class ContractPolishAgent:
    """合同润色助手，使用LangChain分析合同内容"""

    def __init__(self):
        self.llm = llm
        self.grammar_chain = grammar_chain
        self.terminology_chain = terminology_chain
        self.legal_compliance_chain = legal_compliance_chain
        self.completeness_chain = completeness_chain
        self.risk_alert_chain = risk_alert_chain
        self.regulation_query_chain = regulation_query_chain

    def _preprocess_contract(self, contract):
        """预处理合同数据，提取所需信息"""
        # 格式化金额为字符串
        amount_str = str(contract.amount) if contract.amount else "未设置"
        
        # 确保内容不为空
        content = contract.content.strip() if contract.content else "（合同内容为空）"
        if not content:
            content = "（合同内容为空）"
        
        return {
            "title": contract.title or "未命名合同",
            "contract_type": contract.type or "其他",
            "company": contract.company or "未知对方",
            "amount": amount_str,
            "content": content,
        }
        
    def _get_from_cache(self, cache_key):
        """从缓存获取数据"""
        return django_cache.get(cache_key)
        
    def _set_cache(self, cache_key, data):
        """设置缓存数据"""
        django_cache.set(cache_key, data, CACHE_TIMEOUT)

    def polish_contract(self, contract_id, data=None):
        """对合同进行AI润色分析"""
        logger.info(f"开始对合同 {contract_id} 进行AI润色分析")
        start_time = time.time()
        
        # 检查是否为实时分析模式
        is_realtime = data and data.get('is_realtime', False)
        is_manual = data and data.get('is_manual', False)
        
        # 获取个性化参数
        preferences = {}
        if data and 'preferences' in data:
            preferences = data.get('preferences', {})
            logger.info(f"收到个性化参数: {preferences}")
            # 详细记录每个参数
            for key, value in preferences.items():
                logger.info(f"参数 {key}: {value}")
        
        # 如果是手动分析或实时分析，则强制重新分析，不使用缓存
        force_reanalyze = is_realtime or is_manual
        
        # 如果不是强制重新分析，检查缓存和内容变化
        if not force_reanalyze:
            # 获取当前内容和设置
            current_content = None
            if data and 'content' in data:
                current_content = data['content']
            else:
                try:
                    contract = Contract.objects.get(id=contract_id)
                    current_content = contract.content
                except Contract.DoesNotExist:
                    logger.error(f"合同 {contract_id} 不存在")
                    return {"error": "合同不存在"}
            
            # 检查缓存
            cache_key = f"{CACHE_KEY_PREFIX}{contract_id}"
            cached_result = self._get_from_cache(cache_key)
            
            # 同时检查缓存中是否存储了上次分析的内容和设置的哈希值
            cache_hash_key = f"{CACHE_KEY_PREFIX}{contract_id}_hash"
            cached_hash = self._get_from_cache(cache_hash_key)
            
            # 计算当前内容和设置的哈希值
            import hashlib
            current_hash = None
            if current_content:
                content_hash = hashlib.md5(current_content.encode()).hexdigest()
                # 将个性化设置也纳入哈希计算
                settings_str = f"{preferences.get('style', '')}-{preferences.get('contract_type', '')}-{'-'.join(preferences.get('focus', []))}-{'-'.join(preferences.get('custom_terminologies', []))}"
                settings_hash = hashlib.md5(settings_str.encode()).hexdigest()
                current_hash = f"{content_hash}_{settings_hash}"
                logger.info(f"当前内容和设置哈希值: {current_hash}")
            
            # 如果缓存存在且哈希值匹配，则使用缓存
            if cached_result and cached_hash and cached_hash == current_hash:
                logger.info(f"从缓存中获取合同 {contract_id} 的润色分析结果（内容和设置未变化）")
                return cached_result
            elif cached_result:
                if cached_hash:
                    logger.info(f"缓存哈希: {cached_hash}")
                    logger.info(f"当前哈希: {current_hash}")
                    logger.info(f"哈希不匹配，合同 {contract_id} 内容或设置已变化，重新进行分析")
                else:
                    logger.info(f"缓存中没有哈希值，合同 {contract_id} 需要重新分析")
        
        try:
            # 获取合同内容
            content = None
            contract_info = {}
            
            # 如果传入了data且包含content，直接使用data中的content
            if data and 'content' in data:
                content = data['content']
                # 使用默认的合同信息，因为我们只关注内容分析
                contract_info = {
                    'title': '合同文本分析',
                    'contract_type': '通用合同',
                    'company': '',
                    'amount': ''
                }
            else:
                # 否则从数据库获取合同对象
                contract = Contract.objects.get(id=contract_id)
                content = contract.content
                contract_info = self._preprocess_contract(contract)
            
            if not content:
                return {"error": "合同内容为空"}
            
            # 处理个性化参数
            style = preferences.get('style', 'neutral')  # 语言风格：formal/neutral/concise
            contract_type = preferences.get('contract_type', 'general')  # 合同类型
            focus_areas = preferences.get('focus', ['grammar', 'terminology'])  # 优化重点
            custom_terminologies = preferences.get('custom_terminologies', [])  # 自定义术语
            
            # 详细记录个性化参数值
            logger.info(f"处理个性化参数：style={style}, contract_type={contract_type}")
            logger.info(f"优化重点：focus_areas={focus_areas}")
            logger.info(f"自定义术语：custom_terminologies={custom_terminologies}")
            
            # 如果前端传递了合同类型，更新contract_info
            if contract_type != 'general':
                contract_type_map = {
                    'sales': '买卖合同',
                    'labor': '劳务合同',
                    'lease': '租赁合同',
                    'technology': '技术合同',
                    'general': '通用合同'
                }
                contract_info['contract_type'] = contract_type_map.get(contract_type, '通用合同')
            
            # 实时分析模式下，限制处理内容长度和分析复杂度
            if is_realtime:
                # 对于实时分析，只分析较新修改的部分（最后2000个字符）
                content_length = len(content)
                if content_length > 2000:
                    content_to_analyze = content[-2000:]
                    logger.info(f"实时分析模式: 限制分析内容长度为最后2000个字符")
                else:
                    content_to_analyze = content
                
                # 构建个性化提示词
                custom_grammar_prompt = self._build_custom_grammar_prompt(
                    contract_info, style, focus_areas, custom_terminologies
                )
                
                # 创建临时分析链
                temp_prompt = PromptTemplate(
                        input_variables=["title", "contract_type", "company", "amount", "content"],
                        template=custom_grammar_prompt
                )
                # 使用管道运算符创建RunnableSequence
                temp_chain = temp_prompt | llm
                
                # 记录使用的提示词模板
                logger.info(f"使用个性化语法提示词：自定义风格={style}, 合同类型={contract_info['contract_type']}")
                
                # 降低处理复杂度
                grammar_result = temp_chain.invoke({
                    "title": contract_info["title"],
                    "contract_type": contract_info["contract_type"],
                    "company": contract_info["company"],
                    "amount": contract_info["amount"],
                    "content": content_to_analyze
                })
                
                # 确保从AIMessage获取文本内容
                grammar_result_text = _get_message_content(grammar_result)
                
                # 实时模式下仅进行语法分析，不进行术语分析以提高速度
                grammar_suggestions = clean_and_parse_json(grammar_result_text)
                
                # 限制建议数量，提高响应速度
                grammar_suggestions = grammar_suggestions[:5] if len(grammar_suggestions) > 5 else grammar_suggestions
                
                result = {
                    "syntax": grammar_suggestions,
                    "terminology": []
                }
                
                # 实时模式不缓存结果
                logger.info(f"实时润色分析完成，耗时: {time.time() - start_time:.2f}秒")
                return result
            
            # 常规完整分析模式
            result = {"syntax": [], "terminology": []}
            
            # 构建个性化提示词
            custom_grammar_prompt = self._build_custom_grammar_prompt(
                contract_info, style, focus_areas, custom_terminologies
            )
            
            custom_terminology_prompt = self._build_custom_terminology_prompt(
                contract_info, style, focus_areas, custom_terminologies
            )
            
            # 创建临时分析链
            if 'grammar' in focus_areas:
                logger.info(f"使用个性化语法提示词进行分析，风格={style}, 优化重点={focus_areas}")
                # 使用管道运算符创建
                temp_grammar_prompt = PromptTemplate(
                        input_variables=["title", "contract_type", "company", "amount", "content"],
                        template=custom_grammar_prompt
                )
                temp_grammar_chain = temp_grammar_prompt | llm
                
                # 运行语法和格式分析
                grammar_result = temp_grammar_chain.invoke({
                    "title": contract_info["title"],
                    "contract_type": contract_info["contract_type"],
                    "company": contract_info["company"],
                    "amount": contract_info["amount"],
                    "content": content
                })
                # 确保从AIMessage获取文本内容
                grammar_result_text = _get_message_content(grammar_result)
                logger.debug(f"语法分析完成，结果长度: {len(grammar_result_text) if grammar_result_text else 0}")
                
                # 解析结果
                grammar_suggestions = clean_and_parse_json(grammar_result_text)
                result["syntax"] = grammar_suggestions
            
            # 运行术语分析
            if 'terminology' in focus_areas:
                logger.info(f"使用个性化术语提示词进行分析，风格={style}, 优化重点={focus_areas}")
                # 使用管道运算符创建
                temp_terminology_prompt = PromptTemplate(
                        input_variables=["title", "contract_type", "company", "amount", "content"],
                        template=custom_terminology_prompt
                )
                temp_terminology_chain = temp_terminology_prompt | llm
                
                terminology_result = temp_terminology_chain.invoke({
                    "title": contract_info["title"],
                    "contract_type": contract_info["contract_type"],
                    "company": contract_info["company"],
                    "amount": contract_info["amount"],
                    "content": content
                })
                # 确保从AIMessage获取文本内容
                terminology_result_text = _get_message_content(terminology_result)
                logger.debug(f"术语分析完成，结果长度: {len(terminology_result_text) if terminology_result_text else 0}")
                
                # 解析结果
                terminology_suggestions = clean_and_parse_json(terminology_result_text)
                result["terminology"] = terminology_suggestions
            
            # 处理合同润色结果中的HTML实体
            logger.info(f"处理合同{contract_id}润色结果中的HTML实体")
            result = process_polish_result(result)
            
            # 非实时模式才缓存结果
            if not is_realtime:
                # 缓存结果
                cache_key = f"{CACHE_KEY_PREFIX}{contract_id}"
                self._set_cache(cache_key, result)
                
                # 同时缓存内容和设置的哈希值
                # 计算当前内容和设置的哈希值
                import hashlib
                if content:
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    # 将个性化设置也纳入哈希计算
                    settings_str = f"{style}-{contract_type}-{'-'.join(focus_areas)}-{'-'.join(custom_terminologies)}"
                    settings_hash = hashlib.md5(settings_str.encode()).hexdigest()
                    current_hash = f"{content_hash}_{settings_hash}"
                    
                    # 缓存哈希值
                    cache_hash_key = f"{CACHE_KEY_PREFIX}{contract_id}_hash"
                    self._set_cache(cache_hash_key, current_hash)
                    logger.info(f"缓存内容和设置哈希值: {current_hash}")
            
            logger.info(f"合同 {contract_id} 润色分析完成，耗时: {time.time() - start_time:.2f}秒")
            return result
            
        except Contract.DoesNotExist:
            logger.error(f"合同 {contract_id} 不存在")
            return {"error": "合同不存在"}
        except Exception as e:
            logger.exception(f"合同润色分析失败: {str(e)}")
            return {"error": f"润色分析失败: {str(e)}"}
            
    def _build_custom_grammar_prompt(self, contract_info, style, focus_areas, custom_terminologies):
        """根据个性化参数构建语法分析提示词"""
        # 基础语法提示词模板
        prompt = """你是一位专业的合同审核专家，专注于识别并修正合同文本中的语言表达问题。

你的核心任务是，直接提供可替换的优化建议，而不是描述问题。请严格遵循以下要求：

1.  **直接替换**：所有建议都必须是“找到并替换”的形式。`suggested`字段必须能完全替换`original`字段。
2.  **内容优先**：只关注文本内容，忽略所有HTML标签（如`<p>`, `<strong>`等）。不要提出任何关于HTML格式的建议。
3.  **聚焦语言**：仅识别和修正以下语言问题：
    -   标点符号错误
    -   语法结构不当
    -   语句不通顺或存在歧义
    -   指代不明确
    -   表述过于口语化或不严谨

请勿检查或建议任何与HTML格式、间距或布局相关的问题。
"""

        # 根据风格添加额外指导
        if style == 'formal':
            prompt += """
请特别注意文本的正式性和严谨性。文本应当：
- 使用正式、严谨的表达方式
- 避免口语化和非正式表述
- 保持专业、权威的语言风格
- 确保逻辑严密，表述精确
"""
        elif style == 'concise':
            prompt += """
请特别注意文本的简洁性和清晰度。文本应当：
- 使用简洁、直接的表达方式
- 避免冗长、重复的表述
- 保持简明扼要，直达要点
- 确保每句话都有明确的信息传递
"""
        else:  # neutral
            prompt += """
请保持专业的表达方式，同时确保清晰易懂。文本应当：
- 平衡正式性和可读性
- 使用专业术语的同时确保表述清晰
- 保持中性、客观的语言风格
- 注重逻辑性和连贯性
"""

        # 添加自定义术语的处理指导
        if custom_terminologies:
            prompt += "\n以下是需要特别注意的专业术语，请确保它们在文本中被正确使用：\n"
            for term in custom_terminologies:
                prompt += f"- {term}\n"

        # 优化重点处理
        if 'structure' in focus_areas:
            prompt += """
请特别关注句式结构，确保：
- 句子结构完整且逻辑清晰
- 正确使用连接词和过渡短语
- 避免句子过长或过于复杂
- 段落组织合理，主题清晰
"""

        if 'consistency' in focus_areas:
            prompt += """
请特别关注用词一致性，确保：
- 术语在整个文本中使用一致
- 时态、语气和人称保持一致
- 格式和标点符号使用风格统一
- 避免不必要的同义词替换造成混淆
"""

        # 添加合同基本信息部分
        prompt += """
合同基本信息：
标题: {title}
类型: {contract_type}
签约对方: {company}
合同金额: {amount}

合同内容：
{content}

请在合同内容中找出5-10个最明显的语言表达问题。请确保你的建议是具体的文本替换，而不是宽泛的修改意见。

请严格按照以下JSON格式输出，不要有任何前言或说明：
[
  {{
    "original": "应被替换的完整原文本",
    "suggested": "用于替换的完整新文本",
    "explanation": "解释为什么这样修改更好（简洁地说明）"
  }}
]

如果没有发现任何问题，或无法提供直接可替换的建议，请返回一个空数组 []。
"""
        return prompt
        
    def _build_custom_terminology_prompt(self, contract_info, style, focus_areas, custom_terminologies):
        """根据个性化参数构建术语分析提示词"""
        # 基础术语提示词模板
        prompt = """你是一位专业的合同术语专家，专注于识别并修正合同文本中的专业术语使用问题。

你的核心任务是，直接提供可替换的优化建议，而不是描述问题。请严格遵循以下要求：

1.  **直接替换**：所有建议都必须是“找到并替换”的形式。`suggested`字段必须能完全替换`original`字段。
2.  **内容优先**：只关注文本内容，忽略所有HTML标签。不要提出任何关于HTML格式的建议。
3.  **聚焦术语**：仅识别和修正以下术语问题：
    -   非正式或不专业的表述
    -   行业术语使用不当
    -   法律术语使用不准确
    -   可能导致歧义的模糊用语

请勿检查或建议任何与HTML格式、排版或标点相关的问题。
"""

        # 根据风格添加额外指导
        if style == 'formal':
            prompt += """
请特别注意术语的专业性和规范性。建议应当：
- 优先使用正式的法律术语和行业专业词汇
- 确保术语使用符合法律文件的严谨要求
- 避免使用非正式、口语化或模糊的表述
- 保持术语的精确性和权威性
"""
        elif style == 'concise':
            prompt += """
请在保证术语准确性的同时，注重简洁清晰。建议应当：
- 使用精准但易懂的术语表述
- 避免不必要的术语堆砌和复杂表达
- 确保术语使用简明扼要，直达要点
- 平衡专业性和可读性
"""
        else:  # neutral
            prompt += """
请平衡术语的专业性和可理解性。建议应当：
- 使用恰当的专业术语同时保证清晰度
- 在必要时提供简短解释
- 保持术语使用的一致性
- 注重专业准确性和实用性的平衡
"""

        # 添加合同类型的特定指导
        contract_type = contract_info.get('contract_type', '通用合同')
        if '买卖' in contract_type:
            prompt += """
此为买卖合同，请特别关注以下术语的正确使用：
- 标的物、质量标准、交付方式
- 所有权转移、风险承担
- 检验、验收、质量担保
- 违约责任、损失赔偿
"""
        elif '劳务' in contract_type:
            prompt += """
此为劳务合同，请特别关注以下术语的正确使用：
- 服务内容、服务标准、服务期限
- 劳务费用、支付方式、结算周期
- 权利义务、保密要求
- 违约责任、争议解决
"""
        elif '租赁' in contract_type:
            prompt += """
此为租赁合同，请特别关注以下术语的正确使用：
- 租赁物、租赁用途、租期
- 租金、支付方式、押金
- 维修责任、使用限制
- 物业费用、提前终止条件、续租
"""
        elif '技术' in contract_type:
            prompt += """
此为技术合同，请特别关注以下术语的正确使用：
- 技术内容、技术指标、技术标准
- 知识产权归属、保密义务
- 技术服务、技术成果、验收标准
- 侵权责任、技术风险、技术支持
"""

        # 添加自定义术语的处理指导
        if custom_terminologies:
            prompt += "\n以下是需要特别关注的专业术语，请确保它们在文本中被正确使用：\n"
            for term in custom_terminologies:
                prompt += f"- {term}\n"

        # 优化重点处理
        if 'consistency' in focus_areas:
            prompt += """
请特别关注术语的一致性使用，确保：
- 同一概念始终使用相同的术语表述
- 避免术语混用导致的歧义
- 术语使用遵循行业标准和法律规范
- 术语定义清晰且在全文保持一致
"""

        # 添加合同基本信息部分
        prompt += """
合同基本信息：
标题: {title}
类型: {contract_type}
签约对方: {company}
合同金额: {amount}

合同内容：
{content}

请在合同内容中找出3-8个最明显的专业术语使用问题。请确保你的建议是具体的文本替换，而不是宽泛的修改意见。

请严格按照以下JSON格式输出，不要有任何前言或说明：
[
  {{
    "original": "应被替换的完整原文本",
    "suggested": "用于替换的完整新文本",
    "explanation": "解释为什么这样修改更好（简洁地说明）"
  }}
]

如果没有发现任何问题，或无法提供直接可替换的建议，请返回一个空数组 []。
"""
        return prompt

    def invalidate_cache(self, contract_id):
        """清除合同润色结果缓存"""
        # 清除结果缓存
        cache_key = f"{CACHE_KEY_PREFIX}{contract_id}"
        django_cache.delete(cache_key)
        
        # 清除哈希缓存
        cache_hash_key = f"{CACHE_KEY_PREFIX}{contract_id}_hash"
        django_cache.delete(cache_hash_key)
        
        logger.info(f"已清除合同润色缓存及哈希记录, contract_id={contract_id}")

    def check_contract(self, contract_id, data=None):
        """检查合同（AI辅助分析）"""
        logger.info(f"开始对合同 {contract_id} 进行AI检查分析")
        start_time = time.time()
        
        # 记录请求内容摘要
        if data:
            content_length = len(data.get('content', '')) if 'content' in data else 0
            logger.info(f"请求内容长度: {content_length} 字符")
            
            # 获取内容的前100个字符作为日志摘要
            if 'content' in data and data['content']:
                content_preview = data['content'][:100].replace('\n', ' ')
                logger.info(f"内容预览: {content_preview}...")
        
        # 获取个性化参数
        preferences = {}
        check_areas = ['legal_compliance', 'completeness', 'risk_alert']  # 默认全部检查
        check_depth = 'standard'  # 默认标准检查深度
        contract_type = 'general'  # 默认通用合同类型
        
        if data and 'preferences' in data:
            preferences = data.get('preferences', {})
            logger.info(f"收到检查偏好设置: {preferences}")
            
            # 获取检查区域
            if 'check_areas' in preferences and isinstance(preferences['check_areas'], list):
                check_areas = preferences['check_areas']
                logger.info(f"自定义检查区域: {check_areas}")
            else:
                logger.info(f"使用默认检查区域: {check_areas}")
            
            # 获取检查深度
            if 'check_depth' in preferences:
                check_depth = preferences['check_depth']
                logger.info(f"检查深度: {check_depth}")
            else:
                logger.info(f"使用默认检查深度: {check_depth}")
                
            # 获取合同类型
            if 'contract_type' in preferences:
                contract_type = preferences['contract_type']
                logger.info(f"合同类型参考: {contract_type}")
            else:
                logger.info(f"使用默认合同类型: {contract_type}")
        else:
            logger.info(f"未收到任何偏好设置，使用默认值: 检查区域={check_areas}, 深度={check_depth}, 类型={contract_type}")
        
        # 检查缓存
        cache_key = f"contract_check_{contract_id}"
        cached_result = self._get_from_cache(cache_key)
        
        # 计算当前内容和设置的哈希值
        current_hash = None
        if data and 'content' in data:
            import hashlib
            content_hash = hashlib.md5(data['content'].encode()).hexdigest()
            # 将偏好设置纳入哈希计算
            settings_str = f"{contract_type}-{check_depth}-{'-'.join(check_areas)}"
            settings_hash = hashlib.md5(settings_str.encode()).hexdigest()
            current_hash = f"{content_hash}_{settings_hash}"
            
        # 同时检查缓存中是否存储了哈希值
        cache_hash_key = f"contract_check_{contract_id}_hash"
        cached_hash = self._get_from_cache(cache_hash_key)
        
        # 如果缓存存在且哈希值匹配，则使用缓存
        if cached_result and cached_hash and cached_hash == current_hash:
            logger.info(f"从缓存中获取合同 {contract_id} 的检查分析结果（内容和设置未变化）")
            return cached_result
        elif cached_result:
            if cached_hash:
                logger.info(f"缓存哈希: {cached_hash}")
                logger.info(f"当前哈希: {current_hash}")
                logger.info(f"哈希不匹配，合同 {contract_id} 内容或设置已变化，重新进行分析")
            else:
                logger.info(f"缓存中没有哈希值，合同 {contract_id} 需要重新分析")
        
        try:
            # 获取合同内容
            content = None
            contract_info = {}
            
            # 如果传入了data且包含content，直接使用data中的content
            if data and 'content' in data:
                content = data['content']
                # 使用默认的合同信息，因为我们只关注内容分析
                contract_info = {
                    'title': '合同文本分析',
                    'contract_type': contract_type,  # 使用首选项中的合同类型
                    'company': '',
                    'amount': ''
                }
            else:
                # 否则从数据库获取合同对象
                contract = Contract.objects.get(id=contract_id)
                content = contract.content
                contract_info = self._preprocess_contract(contract)
                
                # 更新合同类型为首选项中的值（如果指定）
                if contract_type != 'general':
                    contract_type_map = {
                        'sales': '买卖合同',
                        'labor': '劳务合同',
                        'lease': '租赁合同',
                        'technology': '技术合同',
                        'general': '通用合同'
                    }
                    contract_info['contract_type'] = contract_type_map.get(contract_type, '通用合同')
            
            if not content:
                return {"error": "合同内容为空"}
            
            # 调整模型参数，根据检查深度设置temperature
            temp_value = 0.1  # 默认标准检查的temperature
            if check_depth == 'deep':
                temp_value = 0.05  # 深度检查使用更低的temperature提高确定性
                logger.info("进行深度检查，降低温度以提高精度")
            elif check_depth == 'quick':
                temp_value = 0.2  # 快速检查使用更高的temperature加快生成速度
                logger.info("进行快速检查，提高温度以加快生成")
                
            # 临时改变LLM模型的参数
            temp_llm = ChatOpenAI(
                temperature=temp_value,
                model_name=AI_MODEL,
                openai_api_key=OPENAI_API_KEY,
                openai_api_base=OPENAI_API_BASE
            )
            
            # 分析法律合规性
            legal_issues = []
            if 'legal_compliance' in check_areas:
                logger.info(f"开始分析合同法律合规性, contract_id={contract_id}")
                # 使用管道运算符创建
                legal_prompt = PromptTemplate(
                    input_variables=["title", "contract_type", "company", "amount", "content"],
                    template=legal_compliance_template  # 使用模板文本而非.prompt属性
                )
                legal_chain = legal_prompt | temp_llm
                legal_result = legal_chain.invoke({
                    "title": contract_info["title"],
                    "contract_type": contract_info["contract_type"],
                    "company": contract_info["company"],
                    "amount": contract_info["amount"],
                    "content": content
                })
                # 确保从AIMessage获取文本内容
                legal_result_text = _get_message_content(legal_result)
                legal_issues = clean_and_parse_json(legal_result_text)
            
            # 分析条款完整性
            completeness_issues = []
            if 'completeness' in check_areas:
                logger.info(f"开始分析合同条款完整性, contract_id={contract_id}")
                # 使用管道运算符创建
                completeness_prompt = PromptTemplate(
                    input_variables=["title", "contract_type", "company", "amount", "content"],
                    template=completeness_template  # 使用模板文本而非.prompt属性
                )
                completeness_chain = completeness_prompt | temp_llm
                completeness_result = completeness_chain.invoke({
                    "title": contract_info["title"],
                    "contract_type": contract_info["contract_type"],
                    "company": contract_info["company"],
                    "amount": contract_info["amount"],
                    "content": content
                })
                # 确保从AIMessage获取文本内容
                completeness_result_text = _get_message_content(completeness_result)
                completeness_issues = clean_and_parse_json(completeness_result_text)
            
            # 分析风险提示
            risk_alerts = []
            if 'risk_alert' in check_areas:
                logger.info(f"开始分析合同风险, contract_id={contract_id}")
                # 使用管道运算符创建
                risk_prompt = PromptTemplate(
                    input_variables=["title", "contract_type", "company", "amount", "content"],
                    template=risk_alert_template  # 使用模板文本而非.prompt属性
                )
                risk_chain = risk_prompt | temp_llm
                risk_result = risk_chain.invoke({
                    "title": contract_info["title"],
                    "contract_type": contract_info["contract_type"],
                    "company": contract_info["company"],
                    "amount": contract_info["amount"],
                    "content": content
                })
                # 确保从AIMessage获取文本内容
                risk_result_text = _get_message_content(risk_result)
                risk_alerts = clean_and_parse_json(risk_result_text)
            
            # 计算问题总数
            critical_issues = len(legal_issues)
            warning_issues = len(completeness_issues)
            suggestions = len(risk_alerts)
            total_issues = critical_issues + warning_issues + suggestions
            
            # 构建结果
            result = {
                "totalIssues": total_issues,
                "criticalIssues": critical_issues,
                "warningIssues": warning_issues,
                "suggestions": suggestions,
                "legalComplianceIssues": legal_issues,
                "completenessIssues": completeness_issues,
                "riskAlerts": risk_alerts
            }
            
            # 处理结果中的HTML实体
            logger.info(f"处理合同检查结果中的HTML实体")
            result = process_check_result(result)
            
            # 设置缓存
            self._set_cache(cache_key, result)
            
            # 同时缓存哈希值，用于后续快速比较
            if current_hash:
                self._set_cache(cache_hash_key, current_hash)
                logger.info(f"缓存内容和设置哈希值: {current_hash}")
            
            execution_time = time.time() - start_time
            logger.info(f"合同检查完成, 用时: {execution_time:.2f}s, 总共发现{total_issues}个问题, contract_id={contract_id}")
            
            return result
            
        except Contract.DoesNotExist:
            logger.error(f"合同不存在, contract_id={contract_id}")
            return {"error": "合同不存在"}
        except Exception as e:
            logger.exception(f"合同检查出错: {str(e)}, contract_id={contract_id}")
            return {"error": str(e)}
    
    def invalidate_check_cache(self, contract_id):
        """清除合同检查结果缓存"""
        cache_key = f"contract_check_{contract_id}"
        django_cache.delete(cache_key)
        logger.info(f"已清除合同检查缓存, contract_id={contract_id}")

# 创建润色代理实例
contract_polish_agent = ContractPolishAgent()

# 公开的API方法
def polish_contract(contract_id, data=None):
    """调用合同润色代理进行AI润色分析"""
    agent = ContractPolishAgent()
    return agent.polish_contract(contract_id, data)

def check_contract(contract_id, data=None):
    """调用合同检查代理进行AI检查分析"""
    agent = ContractPolishAgent()
    return agent.check_contract(contract_id, data)

def invalidate_polish_cache(contract_id):
    """清除合同润色缓存的公开方法"""
    contract_polish_agent.invalidate_cache(contract_id)
    
def invalidate_check_cache(contract_id):
    """清除合同检查缓存的公开方法"""
    contract_polish_agent.invalidate_check_cache(contract_id)

# 添加法规查询函数
def query_regulation(data):
    """查询法规相关信息"""
    logger.info(f"开始查询法规信息: {data.get('issue_title', '')}")
    start_time = time.time()
    
    try:
        # 运行法规查询链
        result = regulation_query_chain.invoke({
            "issue_title": data.get('issue_title', ''),
            "issue_content": data.get('issue_content', ''),
            "issue_problem": data.get('issue_problem', ''),
            "contract_type": data.get('contract_type', '通用合同')
        })
        
        # 确保从AIMessage获取文本内容
        result_text = _get_message_content(result)
        
        # 解析结果
        parsed_result = {}
        try:
            # 尝试解析JSON
            parsed_result = json.loads(result_text)
        except json.JSONDecodeError:
            # 如果解析失败，尝试提取关键信息
            logger.warning(f"解析法规查询结果失败，尝试提取关键信息")
            
            # 提取法规名称
            regulation_match = re.search(r'"regulation"\s*:\s*"([^"]+)"', result_text)
            if regulation_match:
                parsed_result['regulation'] = regulation_match.group(1)
            else:
                parsed_result['regulation'] = '《中华人民共和国民法典》'
            
            # 提取法规内容
            content_match = re.search(r'"regulation_content"\s*:\s*"([^"]+)"', result_text)
            if content_match:
                parsed_result['regulation_content'] = content_match.group(1)
            else:
                parsed_result['regulation_content'] = '根据相关法律法规，合同中应明确约定双方权利义务，避免含糊不清的条款。'
            
            # 提取建议
            suggestion_match = re.search(r'"suggestion"\s*:\s*"([^"]+)"', result_text)
            if suggestion_match:
                parsed_result['suggestion'] = suggestion_match.group(1)
            else:
                parsed_result['suggestion'] = '建议参照相关法律法规，明确表述合同条款，确保合同的有效性和可执行性。'
        
        # 处理结果中的HTML实体
        for key in parsed_result:
            if isinstance(parsed_result[key], str):
                parsed_result[key] = process_html_entities(parsed_result[key])
        
        logger.info(f"法规查询完成，耗时: {time.time() - start_time:.2f}秒")
        return parsed_result
        
    except Exception as e:
        logger.exception(f"法规查询失败: {str(e)}")
        return {
            "regulation": "《中华人民共和国民法典》",
            "regulation_content": "根据相关法律法规，合同中应明确约定双方权利义务，避免含糊不清的条款。",
            "suggestion": "建议参照相关法律法规，明确表述合同条款，确保合同的有效性和可执行性。"
        }

# 工具函数：处理文本中的HTML实体
def process_html_entities(text):
    """处理文本中的HTML实体，确保它们被正确解码"""
    if not text:
        return text
    
    # 处理&nbsp;和其他常见HTML实体
    processed = text
    
    # 循环替换所有&nbsp;实体
    while '&nbsp;' in processed:
        processed = processed.replace('&nbsp;', ' ')
    
    # 替换其他空格相关的HTML实体编码
    processed = processed.replace('&#160;', ' ')
    processed = processed.replace('&#xA0;', ' ')
    
    # 使用html模块的unescape函数处理所有HTML实体
    processed = html.unescape(processed)
    
    # 处理其他可能的Unicode空格字符
    special_spaces = [
        '\u00A0',  # 不换行空格
        '\u2002',  # 半角空格
        '\u2003',  # 全角空格
        '\u2004',  # 三分之一空格
        '\u2005',  # 四分之一空格
        '\u2006',  # 六分之一空格
        '\u2007',  # 数字空格
        '\u2008',  # 标点空格
        '\u2009',  # 窄空格
        '\u200A',  # 头发空格
        '\u202F',  # 窄不换行空格
        '\u205F',  # 中度数学空格
    ]
    
    for space in special_spaces:
        processed = processed.replace(space, ' ')
    
    return processed

# 处理检查结果中的所有文本字段
def process_check_result(result):
    """处理检查结果中的所有文本字段，确保没有未解码的HTML实体"""
    if not result or not isinstance(result, dict):
        return result
    
    # 处理法律合规性问题
    if 'legalComplianceIssues' in result and isinstance(result['legalComplianceIssues'], list):
        for issue in result['legalComplianceIssues']:
            if isinstance(issue, dict):
                for key in ['title', 'current', 'problem', 'suggestion']:
                    if key in issue and issue[key]:
                        issue[key] = process_html_entities(issue[key])
    
    # 处理条款完整性问题
    if 'completenessIssues' in result and isinstance(result['completenessIssues'], list):
        for issue in result['completenessIssues']:
            if isinstance(issue, dict):
                for key in ['title', 'suggestion']:
                    if key in issue and issue[key]:
                        issue[key] = process_html_entities(issue[key])
    
    # 处理风险提示
    if 'riskAlerts' in result and isinstance(result['riskAlerts'], list):
        for issue in result['riskAlerts']:
            if isinstance(issue, dict):
                for key in ['title', 'suggestion']:
                    if key in issue and issue[key]:
                        issue[key] = process_html_entities(issue[key])
    
    return result

# 处理润色结果中的所有文本字段
def process_polish_result(result):
    """处理润色结果中的所有文本字段，确保没有未解码的HTML实体"""
    if not result or not isinstance(result, dict):
        return result
    
    # 处理语法和格式建议
    if 'syntax' in result and isinstance(result['syntax'], list):
        for suggestion in result['syntax']:
            if isinstance(suggestion, dict):
                for key in ['original', 'suggested', 'explanation']:
                    if key in suggestion and suggestion[key]:
                        suggestion[key] = process_html_entities(suggestion[key])
    
    # 处理专业术语建议
    if 'terminology' in result and isinstance(result['terminology'], list):
        for suggestion in result['terminology']:
            if isinstance(suggestion, dict):
                for key in ['original', 'suggested', 'explanation']:
                    if key in suggestion and suggestion[key]:
                        suggestion[key] = process_html_entities(suggestion[key])
    
    return result 