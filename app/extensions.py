from flask_sqlalchemy import SQLAlchemy # pyright: ignore[reportMissingImports]
from flask_migrate import Migrate # pyright: ignore[reportMissingModuleSource]
from flask_login import LoginManager # pyright: ignore[reportMissingImports]
from flask_mail import Mail # pyright: ignore[reportMissingImports]
from flask_bcrypt import Bcrypt # pyright: ignore[reportMissingImports]
from flask_limiter import Limiter # pyright: ignore[reportMissingImports]
from flask_limiter.util import get_remote_address # pyright: ignore[reportMissingImports]
from flask_talisman import Talisman # pyright: ignore[reportMissingImports]
from flask_wtf import CSRFProtect
from flask_socketio import SocketIO # pyright: ignore[reportMissingImports]
from authlib.integrations.flask_client import OAuth # pyright: ignore[reportMissingImports]

# Database + migrations
db = SQLAlchemy()
migrate = Migrate()

# Login manager
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.session_protection = "strong"

# Mail
mail = Mail()

# Bcrypt for secure password hashing
bcrypt = Bcrypt()

# Rate limiter - Redis-backed for production, memory for dev
import os
_redis_url = os.getenv('REDIS_URL')
_storage_uri = _redis_url if _redis_url else "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=_storage_uri,
    storage_options={"url": _redis_url} if _redis_url else {}
)


# Security headers / HSTS
talisman = Talisman()

# CSRF protection
csrf = CSRFProtect()

# Socket.IO for real-time updates - WebSocket with polling fallback
import os
async_mode = None
if os.getenv('FLASK_ENV') == 'production':
    try:
        import eventlet  # pyright: ignore[reportMissingImports]
        async_mode = 'eventlet'
    except ImportError:
        try:
            import gevent  # pyright: ignore[reportMissingImports]
            async_mode = 'gevent'
        except ImportError:
            async_mode = 'threading'
else:
    async_mode = 'threading'

socketio = SocketIO(
    # IMPORTANT: Never use "*" in production - specify allowed origins
    cors_allowed_origins=[
        "https://petsona.online",
        "https://www.petsona.online",
        os.getenv('SOCKETIO_CORS_ORIGIN', 'http://localhost:5000')
    ] if os.getenv('FLASK_ENV') == 'production' else "*",
    ping_timeout=60,
    ping_interval=25,
    transports=['websocket', 'polling'],
    async_mode=async_mode,
    manage_session=False,
    engineio_logger=False,
    logger=False,
    # Prevent reconnect storms with exponential backoff
    **({'max_http_buffer_size': 1e6} if os.getenv('FLASK_ENV') == 'production' else {})
)

# OAuth for social login
oauth = OAuth()
