# 添加到文件顶部，确保导入了os模块
import os

# 添加到文件末尾
# GraphRAG配置 - 路径修正为在backend目录下
GRAPHRAG_INPUT_DIR = os.path.join(BASE_DIR, 'graphrag-main', 'ragtest', 'input')
# 确保目录存在
os.makedirs(GRAPHRAG_INPUT_DIR, exist_ok=True)

# 自定义媒体存储配置
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 创建graphrag_files目录，用于存储上传文件
GRAPHRAG_FILES_DIR = os.path.join(MEDIA_ROOT, 'graphrag_files')
os.makedirs(GRAPHRAG_FILES_DIR, exist_ok=True)

# 原始文件存储目录
ORIGINAL_FILES_DIR = os.path.join(MEDIA_ROOT, 'original_files')
os.makedirs(ORIGINAL_FILES_DIR, exist_ok=True) 