from flask import Blueprint # pyright: ignore[reportMissingImports]

bp = Blueprint(
    'profile',
    __name__,
    url_prefix='/profile'
)

from app.profile import routes
