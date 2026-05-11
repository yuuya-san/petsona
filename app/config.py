import os
from datetime import timedelta
from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]

load_dotenv()


class Config:
    """Base config - safe defaults"""

    # =========================
    # CORE SECURITY
    # =========================
    SECRET_KEY = os.getenv("SECRET_KEY") or "fallback-very-strong-key"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Session & cookies - safest defaults
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

    # =========================
    # 🟢 RAILWAY MYSQL CONFIG (PUBLIC - FOR SQLYOG)
    # =========================
    MYSQL_URL = os.getenv("MYSQL_URL")

    if MYSQL_URL:
        SQLALCHEMY_DATABASE_URI = MYSQL_URL.replace(
            "mysql://", "mysql+pymysql://"
        )
    else:
        # Localhost MySQL on port 3307, no password
        SQLALCHEMY_DATABASE_URI = "mysql+pymysql://petsona_user:Petsona-0717@localhost/petsona_db"

    # =========================
    # MAIL
    # =========================
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = "petsona.helpcare@gmail.com"
    MAIL_PASSWORD = "fvgj yfgi aulq squa"
    MAIL_DEFAULT_SENDER = "petsona.helpcare@gmail.com"

    # =========================
    # GOOGLE OAUTH CONFIG
    # =========================
    GOOGLE_CLIENT_ID = "246292318836-fh4abergpjnerh6nj55plpr0lusrqu0q.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET = "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"

    AUTHLIB_INSECURE_TRANSPORT = True

    # =========================
    # RECAPTCHA V3 CONFIG
    # =========================
    # RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY", "6Le4c94sAAAAADh1YOljhLnxWDxvrMbGCDzSXcWT")
    # RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY", "6Le4c94sAAAAAHVDiFrjrGYM6c6bdBs0KhnS72VN")
    # RECAPTCHA_THRESHOLD = float(os.getenv("RECAPTCHA_THRESHOLD", 0.5))

    # =========================
    # FILE UPLOAD
    # =========================
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(__file__),
        'static',
        'uploads',
        'messages'
    )
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024

    @staticmethod
    def init_app(app):
        """Initialize extensions with the app"""
        from app.extensions import oauth

        oauth.register(
            name="google",
            client_id=app.config.get("GOOGLE_CLIENT_ID"),
            client_secret=app.config.get("GOOGLE_CLIENT_SECRET"),
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={
                "scope": "openid email profile"
            }
        )


# =========================
# DEVELOPMENT CONFIG
# =========================
class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False

    # Use local MySQL for development
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://petsona_user:Petsona-0717@localhost/petsona_db"

    RESET_TOKEN_EXPIRY = int(os.getenv("RESET_TOKEN_EXPIRY", 3600))


# =========================
# PRODUCTION CONFIG
# =========================
class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    SQLALCHEMY_DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = timedelta(days=7)

    # Disable insecure transport in production (enforce HTTPS for OAuth)
    AUTHLIB_INSECURE_TRANSPORT = False

    RESET_TOKEN_EXPIRY = int(os.getenv("RESET_TOKEN_EXPIRY", 3600))

    RATELIMIT_DEFAULT = "200 per day"
    RATELIMIT_STRATEGY = "fixed-window"

    MAX_FAILED_LOGIN = int(os.getenv("MAX_FAILED_LOGIN", 5))
    LOCKOUT_TIME = int(os.getenv("LOCKOUT_TIME", 300))

    # CSP removed to prevent internal server errors
    # CSP = {
    #     "default-src": ["'self'"],
    #
    #     "script-src": [
    #         "'self'",
    #         "https://www.google.com",
    #         "https://www.gstatic.com",
    #         "https://unpkg.com",
    #         "https://cdnjs.cloudflare.com",
    #         "lordicon.com"
    #     ],
    #
    #     "style-src": [
    #         "'self'",
    #         "https://fonts.googleapis.com",
    #         "https://cdnjs.cloudflare.com"
    #     ],
    #
    #     "font-src": [
    #         "'self'",
    #         "https://fonts.gstatic.com",
    #         "https://cdnjs.cloudflare.com"
    #     ],
    #
    #     "img-src": [
    #         "'self'",
    #         "data:",
    #         "https://www.google.com",
    #         "https://www.gstatic.com"
    #     ],
    #
    #     "connect-src": [
    #         "'self'",
    #         "https://www.google.com"
    #     ],
    #
    #     "frame-src": [
    #         "https://www.google.com"
    #     ],
    # }

    FRONTEND_URL = os.getenv("FRONTEND_URL", None)
