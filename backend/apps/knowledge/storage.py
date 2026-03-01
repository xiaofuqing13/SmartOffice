"""Custom storage for knowledge files."""

import os
import uuid
import logging
import hashlib
import re
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.apps import apps

logger = logging.getLogger(__name__)

# 设置默认路径
GRAPHRAG_INPUT_DIR = getattr(settings, 'GRAPHRAG_INPUT_DIR', 
                            os.path.join(settings.BASE_DIR, 'graphrag-main', 'ragtest', 'input'))
logger.info(f"GraphRAG存储路径设置为: {GRAPHRAG_INPUT_DIR}")

# 确保目录存在
os.makedirs(GRAPHRAG_INPUT_DIR, exist_ok=True)


class GraphRAGStorage(FileSystemStorage):
    """
    自定义存储类，将文件保存到GraphRAG输入目录
    只允许保存.txt文件，且会检查文件内容是否为有效的文本
    改进版本：增强二进制检测，避免重复文件，改进文件命名策略，增强中文处理
    """
    
    def __init__(self, *args, **kwargs):
        kwargs['location'] = GRAPHRAG_INPUT_DIR
        super().__init__(*args, **kwargs)
    
    def _is_binary_content(self, content):
        """检查内容是否为二进制数据"""
        # 读取内容样本
        try:
            # 如果内容是文件对象，读取前1000个字节
            if hasattr(content, 'read'):
                pos = content.tell()
                sample = content.read(1000)
                content.seek(pos)  # 重置文件指针
            else:
                # 如果是字符串或字节，直接截取
                sample = content[:1000] if len(content) > 1000 else content
                
            # 如果是字节，尝试解码
            if isinstance(sample, bytes):
                try:
                    sample = sample.decode('utf-8', errors='replace')
                except:
                    pass
            
            # 检查是否包含常见二进制文件标志
            binary_markers = ['PK', '%PDF', '\x00', 'Content_Types', 'word/document.xml', 'obj']
            if isinstance(sample, str):
                for marker in binary_markers:
                    if marker in sample:
                        logger.warning(f"检测到二进制标记: {marker}")
                        return True
            
            # 检查非打印字符比例
            if isinstance(sample, str):
                non_printable_ratio = len(re.findall(r'[^\x20-\x7E\u4e00-\u9fff\s\p{P}]', sample, re.UNICODE)) / (len(sample) or 1)
                if non_printable_ratio > 0.2:
                    logger.warning(f"非打印字符比例过高: {non_printable_ratio:.2f}")
                    return True
        except Exception as e:
            logger.error(f"检查二进制内容时出错: {str(e)}")
        
        return False
    
    def _check_for_duplicate(self, content):
        """
        检查是否与已有文件内容重复
        返回: (是否重复, 重复的文件路径)
        """
        try:
            if not content:
                return False, None
                
            # 计算内容哈希
            content_hash = None
            if isinstance(content, bytes):
                content_hash = hashlib.md5(content).hexdigest()
            else:
                # 如果是文件对象，读取内容再计算
                if hasattr(content, 'read'):
                    pos = content.tell()
                    content_bytes = content.read()
                    content.seek(pos)  # 重置文件指针
                    content_hash = hashlib.md5(content_bytes).hexdigest()
                elif isinstance(content, str):
                    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            if not content_hash:
                return False, None
                
            # 检查是否有同样哈希值的文件
            KnowledgeBase = apps.get_model('knowledge', 'KnowledgeBase')
            existing_docs = KnowledgeBase.objects.filter(
                metadata__contains={'content_hash': content_hash[:8]}
            )
            
            if existing_docs.exists():
                for doc in existing_docs:
                    if doc.file and os.path.exists(doc.file.path):
                        logger.info(f"找到内容哈希匹配的文件: {doc.file.path}")
                        return True, doc.file.path
            
            return False, None
        except Exception as e:
            logger.error(f"检查文件重复时出错: {str(e)}")
            return False, None
    
    def _detect_text_encoding(self, content):
        """检测文本内容的编码"""
        try:
            # 如果内容已经是字符串，不需要检测
            if isinstance(content, str):
                return 'utf-8', content
                
            # 转换为字节
            content_bytes = None
            if isinstance(content, bytes):
                content_bytes = content
            elif hasattr(content, 'read'):
                pos = content.tell()
                content_bytes = content.read()
                content.seek(pos)
            
            if not content_bytes:
                return None, None
                
            # 尝试使用chardet检测编码
            try:
                import chardet
                result = chardet.detect(content_bytes)
                encoding = result['encoding']
                confidence = result['confidence']
                logger.info(f"检测到编码: {encoding}, 置信度: {confidence}")
                
                if encoding and confidence > 0.7:
                    try:
                        decoded = content_bytes.decode(encoding)
                        return encoding, decoded
                    except:
                        pass
            except ImportError:
                logger.warning("未安装chardet，无法自动检测编码")
            
            # 尝试常见编码
            for enc in ['utf-8', 'gbk', 'gb2312', 'big5', 'utf-16', 'utf-16le']:
                try:
                    decoded = content_bytes.decode(enc)
                    # 检查解码结果中的中文字符数量
                    chinese_chars = sum(1 for c in decoded[:2000] if '\u4e00' <= c <= '\u9fff')
                    logger.debug(f"使用 {enc} 解码，中文字符数: {chinese_chars}")
                    
                    # 如果包含大量中文字符，很可能是正确的编码
                    if chinese_chars > 10:
                        return enc, decoded
                    
                    # 或者至少内容可读
                    if not self._is_gibberish(decoded[:1000]):
                        return enc, decoded
                except:
                    continue
            
            # 如果无法确定，使用UTF-8加替换字符
            return 'utf-8', content_bytes.decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"检测文本编码时出错: {str(e)}")
            return 'utf-8', None
    
    def _is_gibberish(self, text, threshold=0.3):
        """检查文本是否为乱码"""
        if not text:
            return True
            
        # 计算非有效字符的比例
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,;:!?()[]{}\"'+-*/=<>@#$%^&_ \t\n\r\f")
        valid_chars.update([c for c in text if '\u4e00' <= c <= '\u9fff'])  # 添加中文字符
        
        invalid_count = sum(1 for c in text if c not in valid_chars)
        ratio = invalid_count / len(text)
        
        return ratio > threshold
    
    def _open(self, name, mode='rb'):
        """打开文件时检查是否为txt文件"""
        if not name.lower().endswith('.txt'):
            logger.warning(f"尝试打开非txt文件: {name}，将强制当作文本处理")
        return super()._open(name, mode)
    
    def _save(self, name, content):
        """
        保存文件到GraphRAG输入目录。
        这个简化版本假定文件名已经由调用方（如views.py）处理好，
        并且内容已经是正确的文本格式。
        """
        # 确保文件的父目录存在
        full_path = self.path(name)
        directory = os.path.dirname(full_path)
        os.makedirs(directory, exist_ok=True)
        
        # 直接调用父类方法保存文件，不做任何修改
        return super()._save(name, content)


class OriginalFileStorage(FileSystemStorage):
    """存储原始文件的自定义存储类"""
    
    def _is_binary_content(self, content):
        """检查内容是否为二进制数据"""
        # 读取内容样本
        try:
            # 如果内容是文件对象，读取前1000个字节
            if hasattr(content, 'read'):
                pos = content.tell()
                sample = content.read(1000)
                content.seek(pos)  # 重置文件指针
            else:
                # 如果是字符串或字节，直接截取
                sample = content[:1000] if len(content) > 1000 else content
                
            # 如果是字节，尝试解码
            if isinstance(sample, bytes):
                try:
                    sample = sample.decode('utf-8', errors='replace')
                except:
                    pass
            
            # 检查是否包含常见二进制文件标志
            binary_markers = ['PK', '%PDF', '\x00', 'Content_Types', 'word/document.xml', 'obj']
            if isinstance(sample, str):
                for marker in binary_markers:
                    if marker in sample:
                        logger.warning(f"检测到二进制标记: {marker}")
                        return True
            
            # 检查非打印字符比例
            if isinstance(sample, str):
                non_printable_ratio = len(re.findall(r'[^\x20-\x7E\u4e00-\u9fff\s\p{P}]', sample, re.UNICODE)) / (len(sample) or 1)
                if non_printable_ratio > 0.2:
                    logger.warning(f"非打印字符比例过高: {non_printable_ratio:.2f}")
                    return True
        except Exception as e:
            logger.error(f"检查二进制内容时出错: {str(e)}")
        
        return False
    
    def _check_for_duplicate(self, content):
        """
        检查是否与已有文件内容重复
        返回: (是否重复, 重复的文件路径)
        """
        try:
            if not content:
                return False, None
                
            # 计算内容哈希
            content_hash = None
            if isinstance(content, bytes):
                content_hash = hashlib.md5(content).hexdigest()
            else:
                # 如果是文件对象，读取内容再计算
                if hasattr(content, 'read'):
                    pos = content.tell()
                    content_bytes = content.read()
                    content.seek(pos)  # 重置文件指针
                    content_hash = hashlib.md5(content_bytes).hexdigest()
                elif isinstance(content, str):
                    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            if not content_hash:
                return False, None
                
            # 检查是否有同样哈希值的文件
            KnowledgeBase = apps.get_model('knowledge', 'KnowledgeBase')
            existing_docs = KnowledgeBase.objects.filter(
                metadata__contains={'content_hash': content_hash[:8]}
            )
            
            if existing_docs.exists():
                for doc in existing_docs:
                    if doc.file and os.path.exists(doc.file.path):
                        logger.info(f"找到内容哈希匹配的文件: {doc.file.path}")
                        return True, doc.file.path
            
            return False, None
        except Exception as e:
            logger.error(f"检查文件重复时出错: {str(e)}")
            return False, None
    
    def _detect_text_encoding(self, content):
        """检测文本内容的编码"""
        try:
            # 如果内容已经是字符串，不需要检测
            if isinstance(content, str):
                return 'utf-8', content
                
            # 转换为字节
            content_bytes = None
            if isinstance(content, bytes):
                content_bytes = content
            elif hasattr(content, 'read'):
                pos = content.tell()
                content_bytes = content.read()
                content.seek(pos)
            
            if not content_bytes:
                return None, None
                
            # 尝试使用chardet检测编码
            try:
                import chardet
                result = chardet.detect(content_bytes)
                encoding = result['encoding']
                confidence = result['confidence']
                logger.info(f"检测到编码: {encoding}, 置信度: {confidence}")
                
                if encoding and confidence > 0.7:
                    try:
                        decoded = content_bytes.decode(encoding)
                        return encoding, decoded
                    except:
                        pass
            except ImportError:
                logger.warning("未安装chardet，无法自动检测编码")
            
            # 尝试常见编码
            for enc in ['utf-8', 'gbk', 'gb2312', 'big5', 'utf-16', 'utf-16le']:
                try:
                    decoded = content_bytes.decode(enc)
                    # 检查解码结果中的中文字符数量
                    chinese_chars = sum(1 for c in decoded[:2000] if '\u4e00' <= c <= '\u9fff')
                    logger.debug(f"使用 {enc} 解码，中文字符数: {chinese_chars}")
                    
                    # 如果包含大量中文字符，很可能是正确的编码
                    if chinese_chars > 10:
                        return enc, decoded
                    
                    # 或者至少内容可读
                    if not self._is_gibberish(decoded[:1000]):
                        return enc, decoded
                except:
                    continue
            
            # 如果无法确定，使用UTF-8加替换字符
            return 'utf-8', content_bytes.decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"检测文本编码时出错: {str(e)}")
            return 'utf-8', None
    
    def _is_gibberish(self, text, threshold=0.3):
        """检查文本是否为乱码"""
        if not text:
            return True
            
        # 计算非有效字符的比例
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,;:!?()[]{}\"'+-*/=<>@#$%^&_ \t\n\r\f")
        valid_chars.update([c for c in text if '\u4e00' <= c <= '\u9fff'])  # 添加中文字符
        
        invalid_count = sum(1 for c in text if c not in valid_chars)
        ratio = invalid_count / len(text)
        
        return ratio > threshold
    
    def _open(self, name, mode='rb'):
        """打开文件时检查是否为txt文件"""
        if not name.lower().endswith('.txt'):
            logger.warning(f"尝试打开非txt文件: {name}，将强制当作文本处理")
        return super()._open(name, mode)
    
    def _save(self, name, content):
        """
        保存文件到GraphRAG输入目录。
        这个简化版本假定文件名已经由调用方（如views.py）处理好，
        并且内容已经是正确的文本格式。
        """
        # 确保文件的父目录存在
        full_path = self.path(name)
        directory = os.path.dirname(full_path)
        os.makedirs(directory, exist_ok=True)
        
        # 直接调用父类方法保存文件，不做任何修改
        return super()._save(name, content)
    
    def _detect_file_type(self, content):
        """根据文件内容的魔数检测文件类型"""
        try:
            # 常见文件类型的魔数映射
            magic_numbers = {
                b'%PDF': 'pdf',
                b'PK\x03\x04': 'zip',  # ZIP格式，可能是docx、xlsx等，需进一步区分
                b'\xD0\xCF\x11\xE0': 'ole',  # MS Office旧格式（doc/xls/ppt），需进一步区分
                b'\xFF\xD8\xFF': 'jpg',
                b'\x89PNG': 'png',
                b'GIF8': 'gif',
                b'\x25\x21PS': 'ps',
            }
            
            # 检查文件头
            if isinstance(content, bytes):
                header = content[:10]  # 读取前10个字节作为文件头
                file_type = None
                
                # 先检查主要魔数
                for magic, detected_type in magic_numbers.items():
                    if header.startswith(magic):
                        file_type = detected_type
                        break
                
                # 对ZIP和OLE格式进行进一步区分
                if file_type == 'zip':
                    # 进一步检查ZIP内容以区分docx、xlsx、pptx
                    try:
                        import io
                        import zipfile
                        
                        # 创建内存ZIP文件
                        zip_io = io.BytesIO(content)
                        with zipfile.ZipFile(zip_io) as zip_file:
                            file_list = zip_file.namelist()
                            
                            # 检查特征文件来判断类型
                            if any('word/document.xml' in name for name in file_list):
                                return 'docx'
                            elif any('xl/workbook.xml' in name for name in file_list):
                                return 'xlsx'
                            elif any('ppt/presentation.xml' in name for name in file_list):
                                return 'pptx'
                    except Exception as e:
                        logger.error(f"分析ZIP文件内容时出错: {str(e)}")
                        # 如果无法确定具体类型，返回通用zip类型
                        return 'zip'
                
                # 对OLE格式进一步区分
                elif file_type == 'ole':
                    # 检查内容特征，区分doc/xls/ppt
                    content_str = content[:4096].decode('latin-1', errors='replace')
                    if 'Excel.Sheet' in content_str or 'Worksheet' in content_str:
                        return 'xls'
                    elif 'PowerPoint' in content_str:
                        return 'ppt'
                    elif 'MSWordDoc' in content_str or 'Word.Document' in content_str:
                        return 'doc'
                    # 默认返回doc类型
                    return 'doc'
                
                return file_type
            
            return None
        except Exception as e:
            logger.error(f"检测文件类型时出错: {str(e)}")
            return None

    def _extract_text_from_excel(self, file_path):
        """从Excel文件中提取文本内容"""
        try:
            import tempfile
            text_content = ""
            
            # 尝试使用pandas读取Excel (处理.xlsx和.xls)
            try:
                import pandas as pd
                
                # 读取所有工作表
                excel_data = pd.read_excel(file_path, sheet_name=None, header=None)
                
                # 遍历每个工作表
                for sheet_name, df in excel_data.items():
                    text_content += f"\n## 工作表: {sheet_name}\n\n"
                    
                    # 将工作表数据转换为字符串
                    sheet_text = df.to_string(index=False, header=False, na_rep="")
                    text_content += sheet_text + "\n\n"
                
                if text_content:
                    logger.info(f"使用pandas成功从Excel提取文本，长度: {len(text_content)}")
                    return text_content
            except Exception as e:
                logger.error(f"使用pandas提取Excel内容失败: {str(e)}")
            
            # 如果pandas失败，尝试使用textract
            try:
                import textract
                excel_bytes = textract.process(file_path, extension=os.path.splitext(file_path)[1][1:])
                text_content = excel_bytes.decode('utf-8', errors='replace')
                logger.info(f"使用textract从Excel提取文本，长度: {len(text_content)}")
                return text_content
            except Exception as e:
                logger.error(f"使用textract提取Excel内容失败: {str(e)}")
            
            # 所有方法都失败
            return "无法提取Excel文件内容。请安装pandas或textract库。"
            
        except Exception as e:
            logger.error(f"提取Excel文本时出错: {str(e)}")
            return f"Excel文本提取失败: {str(e)}"