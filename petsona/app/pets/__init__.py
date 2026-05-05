from flask import Blueprint # pyright: ignore[reportMissingImports]

bp = Blueprint(
    'pets',
    __name__,
    url_prefix='/pets'
)

from app.pets import routes
