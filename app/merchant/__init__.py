from flask import Blueprint # pyright: ignore[reportMissingImports]

bp = Blueprint(
    'merchant',
    __name__,
    url_prefix='/merchant'
)

from app.merchant import routes
