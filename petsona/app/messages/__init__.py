"""Messages blueprint."""
from flask import Blueprint # pyright: ignore[reportMissingImports]

bp = Blueprint('messages', __name__, url_prefix='/messages')

from . import routes
