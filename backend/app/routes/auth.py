from flask import Blueprint

bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# TODO: Implement authentication routes 