from pathlib import Path

# BASE_DIR apunta al directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "tu-secret-key"
DEBUG = True
ALLOWED_HOSTS = []

# Aplicaciones instaladas
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    "accounts",   # tu app de usuarios
    "busqueda",   # tu app de búsqueda
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# Plantillas
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Aquí puedes agregar rutas globales de templates si quieres
        "DIRS": [BASE_DIR / "templates"],  # carpeta global opcional
        "APP_DIRS": True,  # ✅ importante para buscar templates dentro de cada app
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Base de datos
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Validadores de contraseña
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internacionalización
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# Archivos estáticos
STATIC_URL = "static/"

# Modelo de usuario personalizado
AUTH_USER_MODEL = "accounts.User"

# Auto field por defecto
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# URLs de login
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Opcional: carpeta global de templates (si quieres)
# BASE_DIR / "templates"
# Estructura recomendada:
# Gestor-de-citas/
# ├─ templates/         <-- aquí tus templates globales (opcional)
# └─ busqueda/
#    └─ templates/
#       └─ busqueda/
#          └─ tabla_disponibilidad.html  <-- así Django la encuentra