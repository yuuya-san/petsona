from flask import Blueprint # pyright: ignore[reportMissingImports]

bp = Blueprint(
    'admin',
    __name__,
    url_prefix='/admin'
)

from app.admin import routes
