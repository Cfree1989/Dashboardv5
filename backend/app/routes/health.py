from __future__ import annotations
from flask import Blueprint, jsonify, current_app
from app import db
from sqlalchemy import text


bp = Blueprint('health', __name__, url_prefix='/api/v1')


@bp.route('/health', methods=['GET'])
def api_health():
    components = {
        'database': 'unknown',
        'workers': 'unknown',
    }
    status = 'ok'

    # Database check: simple SELECT 1
    try:
        with db.engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        components['database'] = 'ok'
    except Exception:
        components['database'] = 'error'
        status = 'error'

    # Worker/broker check (placeholder — no Redis wiring in tests)
    # Keep it as 'unknown' to avoid false negatives during local dev/tests

    payload = {
        'status': status,
        'components': components,
        'env': 'testing' if current_app.config.get('TESTING') else 'production-like',
    }
    http_code = 200 if status == 'ok' else 503
    return jsonify(payload), http_code


