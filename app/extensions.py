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

# Rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


# Security headers / HSTS
talisman = Talisman()

# CSRF protection
csrf = CSRFProtect()

# Socket.IO for real-time updates - WebSocket with polling fallback
# Allow Flask-SocketIO to select the best async mode available.
# For production, eventlet is preferred when installed.

def _select_socketio_async_mode():
    try:
        import eventlet  # pyright: ignore[reportMissingImports, reportMissingModuleSource]
        return 'eventlet'
    except ImportError:
        pass
    try:
        import gevent  # pyright: ignore[reportMissingModuleSource]
        return 'gevent'
    except ImportError:
        pass
    return None

socketio = SocketIO(
    cors_allowed_origins="*",
    ping_timeout=60,  # Increased timeout to prevent disconnects
    ping_interval=25,
    transports=['websocket', 'polling'],  # WebSocket first, fallback to polling if needed
    async_mode=_select_socketio_async_mode(),
    engineio_logger=False,  # Disable debug logging
    logger=False,
)

# OAuth for social login
oauth = OAuth()
