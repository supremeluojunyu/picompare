import os
from pathlib import Path

import environ

env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY', default='dev-secret-change-me')
# Oracle 照片同步配置中的密码加密（Fernet，见 cryptography）；留空则用 SECRET_KEY 派生（生产建议单独配置并备份）
ORACLE_SYNC_FERNET_KEY = env('ORACLE_SYNC_FERNET_KEY', default='').strip() or None
DEBUG = env.bool('DEBUG', default=True)
ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=[
        'http://127.0.0.1:8000',
        'http://127.0.0.1:8765',
        'http://localhost:8000',
        'http://localhost:8765',
    ],
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'captcha',
    'rest_framework',
    'corsheaders',
    'celery',
    'django_celery_results',
    'django_celery_beat',
    'photo_access',
    'users',
    'photos',
    'configs',
    'audit',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'audit.middleware.AuditMiddleware',
]

ROOT_URLCONF = 'photo_site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'photo_site.wsgi.application'

USE_ORACLE = env.bool('USE_ORACLE', default=False)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
}
if USE_ORACLE:
    DATABASES['oracle'] = {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': env('ORACLE_NAME'),
        'USER': env('ORACLE_USER'),
        'PASSWORD': env('ORACLE_PASSWORD'),
        'HOST': env('ORACLE_HOST'),
        'PORT': env('ORACLE_PORT'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {'threaded': True, 'encoding': 'UTF-8', 'nencoding': 'UTF-8'},
    }
    DATABASE_ROUTERS = ['photo_site.db_router.OracleRouter']
else:
    DATABASE_ROUTERS = []

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / 'locale']

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
PHOTO_STORAGE_DIR = MEDIA_ROOT / 'person_photos'
os.makedirs(PHOTO_STORAGE_DIR, exist_ok=True)

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
# 无 Redis 时改为 True，上传任务同步执行（虚拟机仅跑网站时可如此）
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=True)
CELERY_TASK_EAGER_PROPAGATES = True

LOG_DIR = BASE_DIR / 'logs'
os.makedirs(LOG_DIR, exist_ok=True)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
}

PHOTO_MAX_SIZE_MB = env.int('PHOTO_MAX_SIZE_MB', default=5)
CLARITY_THRESHOLD = env.int('CLARITY_THRESHOLD', default=100)
BACKGROUND_ALLOWED_COLORS = [
    {'r_min': 200, 'r_max': 255, 'g_min': 200, 'g_max': 255, 'b_min': 200, 'b_max': 255}
]
FACE_SIMILARITY_THRESHOLD = env.float('FACE_SIMILARITY_THRESHOLD', default=0.85)
PHOTO_ALLOW_FIRST_AS_BASELINE = env.bool('PHOTO_ALLOW_FIRST_AS_BASELINE', default=True)
PHOTO_BASELINE_REQUIRE_FACE = env.bool('PHOTO_BASELINE_REQUIRE_FACE', default=False)
NUMBER_FIELD = env('NUMBER_FIELD', default='id_card')
INSIGHTFACE_MODEL = env('INSIGHTFACE_MODEL', default='buffalo_l')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.math_challenge'
CAPTCHA_TIMEOUT = 5
