from flask import Blueprint, jsonify
from app.utils.decorators import token_required
from app import db
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint('diag', __name__, url_prefix='/api/v1/_diag')


@bp.route('', methods=['GET'])
@token_required
def diagnostics():
    info = {
        'db_engine': None,
        'db_url_sanitized': None,
        'migration_head': None,
        'job_counts_by_status': {},
        'app_env': 'testing' if db.get_app().config.get('TESTING') else 'production-like',
    }

    try:
        engine = db.engine
        info['db_engine'] = engine.name
        uri = db.get_app().config.get('SQLALCHEMY_DATABASE_URI', '')
        # sanitize credentials
        import re
        info['db_url_sanitized'] = re.sub(r'(://[^:/@]+):[^@]*@', r'\1:***@', uri)
    except Exception:
        pass

    # Attempt to read Alembic version if table exists
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT version_num FROM alembic_version LIMIT 1
            """))
            row = result.first()
            if row:
                info['migration_head'] = row[0]
    except SQLAlchemyError:
        info['migration_head'] = None

    # Job counts by status
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT status, COUNT(*) FROM job GROUP BY status
            """))
            info['job_counts_by_status'] = {row[0]: int(row[1]) for row in result}
    except SQLAlchemyError:
        info['job_counts_by_status'] = {}

    return jsonify(info), 200


