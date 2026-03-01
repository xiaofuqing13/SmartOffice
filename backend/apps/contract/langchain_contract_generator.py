"""
LangChain合同生成代理
根据用户的一句话描述，生成完整合同内容
"""

import logging
import os
import re
import json
import time
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_community.cache import InMemoryCache
from langchain.globals import set_llm_cache
from langchain.schema import HumanMessage
from langchain_core.runnables import RunnableSequence
from django.conf import settings
from .models import Contract, ContractAction
import traceback

# 配置日志
logger = logging.getLogger(__name__)

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
try:
    # 尝试使用新版本的LangChain API
    llm = ChatOpenAI(
        temperature=0.7,
        model_name=AI_MODEL,  # 使用配置文件中指定的模型
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_API_BASE,
        request_timeout=180,  # 设置更长的请求超时时间（秒）
        max_retries=3  # 添加自动重试机制
    )
    logger.info("使用新版本LangChain API初始化LLM成功")
except Exception as e:
    logger.warning(f"使用新版API初始化LLM失败: {str(e)}，尝试旧版API")
    try:
        # 回退到旧版本的LangChain API
        llm = ChatOpenAI(
            temperature=0.7,
            model_name=AI_MODEL,  # 使用配置文件中指定的模型
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_API_BASE,
            request_timeout=180,  # 设置更长的请求超时时间（秒）
            max_retries=3  # 添加自动重试机制
        )
        logger.info("使用旧版本LangChain API初始化LLM成功")
    except Exception as old_e:
        logger.error(f"初始化LLM失败: {str(old_e)}")
        raise RuntimeError("无法初始化LLM模型，请检查API配置")

# 合同生成提示模板
contract_generation_template = """你是一位专业的合同撰写AI Agent，能够根据用户的需求生成符合法律规范和行业标准的合同。
你的任务是根据用户的一句话描述，生成一份完整、专业、合法的合同文本，包括所有必要的条款。

用户的合同需求描述: {description}

请生成一份完整的合同内容，要求如下：
1. 提取描述中的关键信息，如合同类型、甲方乙方信息、交易内容、金额、时间等；
2. 合同应包括但不限于：合同标题、甲乙双方信息、合同目的、权利义务、付款条件、交付条款、保密条款、违约责任、争议解决和合同期限等标准条款；
3. 使用专业、规范的法律语言，确保合同条款清晰、无歧义；
4. 合同格式应规范，包括条款编号、标点符号使用等；
5. 将所有重要的业务信息和条件纳入合同条款中；
6. 保持文档的HTML格式，使用<h1>、<h2>、<p>等标签来组织文档结构；
7. 如果用户描述中信息不足，请合理补充必要的默认条款。

同时，请从用户的描述中提取并返回以下合同元数据（JSON格式）：
1. 合同标题
2. 合同类型（如销售合同、服务协议、租赁合同等）
3. 甲方名称
4. 乙方名称
5. 预估合同金额（如能确定）

### 输出格式 ###
请按如下格式返回：

```metadata
{{
  "title": "合同标题",
  "type": "合同类型",
  "party_a": "甲方名称",
  "party_b": "乙方名称",
  "amount": "预估金额(只需数字，如无法确定则为0)"
}}
```

```contract
[合同全文，使用HTML格式，包含所有必要条款]
```
"""

# 创建生成合同的Chain
contract_generation_prompt = PromptTemplate(
    input_variables=["description"],
    template=contract_generation_template
)

# 使用|运算符替代LLMChain
contract_generation_chain = contract_generation_prompt | llm

def extract_contract_parts(text):
    """从生成的文本中提取元数据和合同内容"""
    try:
        logger.info(f"开始提取合同内容，文本长度: {len(text)}")
        
        # 1. 尝试提取标准的metadata和contract块
        metadata_match = re.search(r'```metadata\s*([\s\S]*?)\s*```', text, re.DOTALL)
        contract_match = re.search(r'```contract\s*([\s\S]*?)\s*```', text, re.DOTALL)

        if metadata_match and contract_match:
            metadata_json = metadata_match.group(1).strip()
            contract_content = contract_match.group(1).strip()
            logger.info("成功提取到标准格式的metadata和contract内容")
        else:
            # 2. 如果标准格式失败，尝试寻找任何JSON块作为元数据
            logger.warning("未找到标准格式，尝试寻找JSON块")
            json_match = re.search(r'\{[\s\S]*?\}', text, re.DOTALL)
            if json_match:
                metadata_json = json_match.group(0)
                # 剩余部分作为合同内容
                contract_content = text[json_match.end():].strip()
                logger.info("找到JSON块作为元数据")
            else:
                # 3. 如果还是失败，使用默认元数据，并将全部文本作为内容
                logger.warning("未找到任何JSON块，使用默认元数据")
                metadata_json = '{}' # 空JSON
                contract_content = text

        # 解析元数据
        try:
            metadata = json.loads(metadata_json)
        except json.JSONDecodeError:
            logger.error(f"元数据JSON解析失败: {metadata_json[:100]}...")
            metadata = {} # 空字典
        
        # 填充默认元数据
        default_metadata = {
            "title": "AI生成的合同",
            "type": "其他",
            "party_a": "甲方",
            "party_b": "乙方",
            "amount": "0"
        }
        # 使用默认值更新解析到的元数据
        default_metadata.update(metadata)
        metadata = default_metadata
        
        # 如果合同内容为空，则将原始文本作为内容
        if not contract_content.strip():
            contract_content = text

        return metadata, contract_content
        
    except Exception as e:
        logger.error(f"提取合同部分时发生严重错误: {e}", exc_info=True)
        # 返回绝对安全的默认值
        return {
            "title": "处理失败", "type": "错误", "party_a": "", "party_b": "", "amount": "0"
        }, f"<h1>提取内容失败</h1><p>系统在解析AI返回结果时出错。</p><p>错误: {e}</p>"

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

class ContractGeneratorAgent:
    """合同生成代理类"""
    
    def __init__(self):
        self.chain = contract_generation_chain
    
    def generate_contract(self, description):
        """根据描述生成合同"""
        try:
            logger.info(f"开始生成合同. 描述: {description[:100]}...")
            start_time = time.time()
            
            # 统一使用最稳定和兼容的invoke方法
            response = self.chain.invoke({"description": description})
            result = _get_message_content(response)
                
            if not result:
                raise Exception("AI模型返回了空内容")
                    
            generation_time = time.time() - start_time
            logger.info(f"合同生成完成，耗时: {generation_time:.2f}秒")
            
            # 提取元数据和合同内容
            metadata, content = extract_contract_parts(result)
            
            return { "metadata": metadata, "content": content }
        
        except Exception as e:
            logger.error(f"生成合同时发生严重错误: {e}", exc_info=True)
            # 返回包含错误信息的安全默认值
            return {
                "metadata": {
                    "title": "AI合同生成失败",
                    "type": "错误",
                    "party_a": "",
                    "party_b": "",
                    "amount": "0"
                },
                "content": f"<h1>AI合同生成失败</h1><p>系统在调用AI服务时遇到问题，请稍后重试或联系管理员。</p><p>错误详情: {e}</p>"
            }

# 单例模式
contract_generator = ContractGeneratorAgent()

def generate_contract(description):
    """生成合同的便捷函数"""
    return contract_generator.generate_contract(description) 