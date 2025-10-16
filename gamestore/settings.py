"""
Django settings for gamestore project.
"""
from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Memuat variabel dari file .env
load_dotenv(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')

allowed_hosts_str = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = ['.vercel.app', 'main-ajaa.vercel.app']

csrf_origins_str = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_origins_str.split(',') if origin.strip()]

INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'main', 'theme', 'widget_tweaks', 'tailwind', 'allauth', 'allauth.account',
    'allauth.socialaccount', 'django.contrib.sites',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'gamestore.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
WSGI_APPLICATION = 'gamestore.wsgi.application'

# ===============================================
# DATABASE & PASSWORD
# ===============================================
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('POSTGRES_URL', f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
        conn_max_age=600
    )
}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===============================================
# I18N & FILES
# ===============================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ===============================================
# TAILWIND & LAINNYA
# ===============================================
TAILWIND_APP_NAME = 'theme'
NPM_BIN_PATH = "/usr/local/bin/npm"
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# PERBAIKAN DI SINI: Tambahkan pengecekan sebelum .encode()
encryption_key_str = os.environ.get('ENCRYPTION_KEY')
if not encryption_key_str:
    raise ValueError("ERROR: ENCRYPTION_KEY tidak ditemukan. Pastikan ada di file .env Anda.")
ENCRYPTION_KEY = encryption_key_str.encode()

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
SITE_ID = 1
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
ACCOUNT_AUTHENTICATION_METHOD = 'username_email' 
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True 

# Konfigurasi Midtrans diambil dari .env
MIDTRANS_SERVER_KEY = os.environ.get('MIDTRANS_SERVER_KEY')
MIDTRANS_CLIENT_KEY = os.environ.get('MIDTRANS_CLIENT_KEY')
MIDTRANS_IS_PRODUCTION = os.environ.get('MIDTRANS_IS_PRODUCTION', 'False').lower() in ('true', '1', 't')
