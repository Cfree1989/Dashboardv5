from flask import Blueprint, jsonify, current_app, request
from app.utils.decorators import token_required
from app import db
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.models.job import Job
from sqlalchemy import func
from app.business_logic.shared_services import email_service
from app.business_logic.shared_services.response_service import ResponseService, ErrorCategory, ErrorCode

bp = Blueprint('diag', __name__, url_prefix='/api/v1/_diag')


def _is_email_configured():
    """Check if email is properly configured."""
    return all([
        current_app.config.get('MAIL_SERVER'),
        current_app.config.get('MAIL_USERNAME'),
        current_app.config.get('MAIL_DEFAULT_SENDER')
    ])


def send_email(subject, recipients, html_body, text_body):
    """Send an email using the email service."""
    try:
        return email_service.send_email(subject, recipients, html_body, text_body)
    except Exception:
        return False


@bp.route('', methods=['GET'])
@token_required
def diagnostics():
    info = {
        'db_engine': None,
        'db_url_sanitized': None,
        'migration_head': None,
        'job_counts_by_status': {},
        'app_env': 'testing' if current_app.config.get('TESTING') else 'production-like',
        'email_configured': _is_email_configured(),
        'email_config': {
            'MAIL_SERVER': current_app.config.get('MAIL_SERVER'),
            'MAIL_USERNAME': '***SET***' if current_app.config.get('MAIL_USERNAME') else None,
            'MAIL_DEFAULT_SENDER': current_app.config.get('MAIL_DEFAULT_SENDER'),
        }
    }

    try:
        engine = db.engine
        info['db_engine'] = engine.name
        uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
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

    # Job counts by status via ORM (safer across engines)
    try:
        rows = db.session.query(Job.status, func.count()).group_by(Job.status).all()
        info['job_counts_by_status'] = {status: int(count) for status, count in rows}
    except SQLAlchemyError:
        info['job_counts_by_status'] = {}

    return jsonify(info), 200


@bp.route('/test-email', methods=['POST'])
@token_required
def test_email():
    """Test email configuration by sending a test email."""
    data = request.get_json() or {}
    test_email = data.get('email')
    
    if not test_email:
        return ResponseService.validation_error(
            message='email parameter required',
            error_code=ErrorCode.MISSING_REQUIRED_FIELD.value
        )
    
    # Check if email is configured
    if not _is_email_configured():
        return ResponseService.validation_error(
            message='Email not configured',
            error_code=ErrorCode.INVALID_VALUE.value,
            details={
                'missing': {
                    'MAIL_SERVER': not current_app.config.get('MAIL_SERVER'),
                    'MAIL_USERNAME': not current_app.config.get('MAIL_USERNAME'),
                    'MAIL_DEFAULT_SENDER': not current_app.config.get('MAIL_DEFAULT_SENDER'),
                }
            }
        )
    
    # Send test email
    subject = "3D Print System - Email Test"
    html_body = """
    <h2>Email Test Successful</h2>
    <p>This is a test email from your 3D Print Management System.</p>
    <p>If you received this, your email configuration is working correctly!</p>
    """
    text_body = "Email Test Successful\n\nThis is a test email from your 3D Print Management System.\n\nIf you received this, your email configuration is working correctly!"
    
    success = send_email(subject, [test_email], html_body, text_body)
    
    if success:
        return ResponseService.success({
            'message': 'Test email sent successfully',
            'to': test_email
        })
    else:
        return ResponseService.server_error(
            message='Failed to send test email',
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR.value,
            details={'check_logs': True}
        )
