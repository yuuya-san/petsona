from flask import Blueprint # pyright: ignore[reportMissingImports]

bp = Blueprint(
    'matching',
    __name__,
    url_prefix='/matching'
)

from app.matching import routes
