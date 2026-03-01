"""
Django settings for smart-office project.
"""

import os
import yaml
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载YAML配置文件
config_path = os.path.join(BASE_DIR, 'setting.yaml')
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config['django']['secret_key']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config['django']['debug']

ALLOWED_HOSTS = config['django']['allowed_hosts']

# 默认不追加反斜杠，允许无斜线URL
APPEND_SLASH = False

# 调试模式下禁用CSRF保护 - 仅用于开发环境!
if DEBUG:
    CSRF_COOKIE_SECURE = False
    CSRF_COOKIE_HTTPONLY = False
    CSRF_USE_SESSIONS = False

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 第三方应用
    'rest_framework',
    'corsheaders',
    'drf_yasg',
    'django_filters',
    
    # 自定义应用
    'apps.users',
    'apps.calendar',
    'apps.chat',
    'apps.knowledge',
    'apps.ai',
    'apps.contract',  # 添加合同管理应用
    'apps.setting',   # 添加设置应用
    'apps.smartdoc',  # 添加智能文档应用
    'apps.project',   # 添加项目管理应用
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # 确保CORS中间件位于最前面
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # 可能需要禁用此中间件进行测试
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# Docker 环境下优先从环境变量读取，本地开发则使用 setting.yaml
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', config['database']['name']),
        'USER': os.environ.get('DB_USER', config['database']['user']),
        'PASSWORD': os.environ.get('DB_PASSWORD', config['database']['password']),
        'HOST': os.environ.get('DB_HOST', config['database']['host']),
        'PORT': os.environ.get('DB_PORT', config['database']['port']),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = False

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.users.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # 添加会话认证作为备选
        'rest_framework.authentication.BasicAuthentication',  # 添加基本认证
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'UNAUTHENTICATED_USER': None,  # 默认匿名用户
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# CSRF配置
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8080',
    'http://127.0.0.1:8080', 
    'http://localhost:8081',
    'http://127.0.0.1:8081',
]
CSRF_COOKIE_SECURE = False  # 开发环境设置为False
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False
# 关闭CSRF保护用于API测试（仅开发环境）
CSRF_COOKIE_NAME = 'csrftoken'

# JWT Settings
JWT_AUTH = {
    'JWT_SECRET_KEY': SECRET_KEY,
    'JWT_ALGORITHM': 'HS256',
    'JWT_VERIFY': True,
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_EXPIRATION_DELTA': 60 * 60 * 24 * 7,  # 7 days
}

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True  # 开发环境中允许所有跨域请求
CORS_ALLOW_CREDENTIALS = True  # 允许跨域请求携带凭证
CORS_ALLOWED_ORIGINS = config['cors']['allowed_origins'] + [
    'http://localhost:8081',
    'http://127.0.0.1:8081',
    'http://localhost:8080',
    'http://127.0.0.1:8080',
]

# 允许的HTTP方法
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# 允许的HTTP头
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# AI Settings
OPENAI_API_KEY = config['ai']['openai_api_key']
OPENAI_API_BASE = config['ai']['openai_api_base']
AI_MODEL = config['ai']['model']

# 添加原始文件存储目录配置
ORIGINAL_FILES_DIR = os.path.join(BASE_DIR, 'media', 'original_files')
os.makedirs(ORIGINAL_FILES_DIR, exist_ok=True)

# 配置日志
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module}.{funcName}: {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
} 