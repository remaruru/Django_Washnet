"""
Django settings for laundry_pos project.
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ── Security ─────────────────────────────────────────────────────────────────

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    default='django-insecure-n54zq)3@g185c7sc1ivbp_6jq(i%5nwonk2wy!%ppqvhp*f=_0'
)

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.onrender.com',  # Allow all Render subdomains
]


# ── Application definition ────────────────────────────────────────────────────

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'corsheaders',

    # Local apps
    'core',

    # Cloudinary Integration
    'cloudinary_storage',
    'cloudinary',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'laundry_pos.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'laundry_pos.wsgi.application'


# ── Database ──────────────────────────────────────────────────────────────────
# Uses PostgreSQL on Render (via DATABASE_URL env var), falls back to SQLite locally.

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=not DEBUG,
    )
}


# ── Password validation ───────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ── Internationalization ──────────────────────────────────────────────────────

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Manila'

USE_I18N = True

USE_TZ = True


# ── Static files ──────────────────────────────────────────────────────────────

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise compression and caching
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ── Media files ───────────────────────────────────────────────────────────────

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cloudinary Storage for uploaded media (QR codes)
if os.environ.get('CLOUDINARY_URL'):
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'


# ── Auth ──────────────────────────────────────────────────────────────────────

AUTH_USER_MODEL = 'core.User'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'


# ── CORS ──────────────────────────────────────────────────────────────────────

CORS_ALLOW_ALL_ORIGINS = True


# ── AI Chatbot ────────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
