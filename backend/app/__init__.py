from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
import os
import re

db = SQLAlchemy(session_options={"expire_on_commit": False})
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_EXPIRE_ON_COMMIT'] = False
    # Guardrail: avoid accidental SQLite fallback in non-test runs
    if not app.config.get('TESTING') and 'DATABASE_URL' not in os.environ:
        raise RuntimeError('DATABASE_URL is not set. Refusing to start to avoid SQLite fallback.')
    
    # JWT Cookie Configuration
    app.config['JWT_COOKIE_NAME'] = os.environ.get('JWT_COOKIE_NAME', 'auth_token')
    app.config['JWT_COOKIE_SECURE'] = os.environ.get('JWT_COOKIE_SECURE', 'false').lower() == 'true'
    app.config['JWT_COOKIE_HTTPONLY'] = os.environ.get('JWT_COOKIE_HTTPONLY', 'true').lower() == 'true'
    app.config['JWT_COOKIE_SAMESITE'] = os.environ.get('JWT_COOKIE_SAMESITE', 'Lax')
    app.config['JWT_COOKIE_DOMAIN'] = os.environ.get('JWT_COOKIE_DOMAIN', None)
    app.config['JWT_COOKIE_PATH'] = os.environ.get('JWT_COOKIE_PATH', '/')
    app.config['JWT_COOKIE_MAX_AGE'] = int(os.environ.get('JWT_COOKIE_MAX_AGE', 43200))  # 12 hours in seconds
    
    # Email configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.office365.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    # Optional: disable sending in tests if no config is provided
    if app.config.get('TESTING'):
        app.config.setdefault('MAIL_SUPPRESS_SEND', True)
    
    # Initialize extensions
    db.init_app(app)
    # Prevent attribute expiration on commit for detached instances in tests
    db.session.expire_on_commit = False
    migrate.init_app(app, db)
    CORS(app)
    limiter.init_app(app)
    mail.init_app(app)
    
    # Error response middleware for standardized error formatting
    # Import here to avoid circular imports
    from app.business_logic.shared_services.response_service import ResponseService, ErrorCategory, ErrorCode
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors"""
        return ResponseService.validation_error(
            message="Bad request",
            error_code=ErrorCode.INVALID_INPUT.value,
            details={'description': str(error)}
        )
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors"""
        return ResponseService.unauthorized(
            message="Unauthorized",
            error_code=ErrorCode.UNAUTHORIZED.value
        )
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors"""
        return ResponseService.forbidden(
            message="Forbidden",
            error_code=ErrorCode.FORBIDDEN.value
        )
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        return ResponseService.not_found(
            resource="Resource",
            error_code=ErrorCode.RESOURCE_NOT_FOUND.value
        )
    
    @app.errorhandler(409)
    def conflict(error):
        """Handle 409 Conflict errors"""
        return ResponseService.conflict(
            message="Resource conflict",
            error_code=ErrorCode.RESOURCE_CONFLICT.value
        )
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle 422 Unprocessable Entity errors"""
        return ResponseService.business_error(
            message="Unprocessable entity",
            error_code=ErrorCode.BUSINESS_RULE_VIOLATION.value
        )
    
    @app.errorhandler(429)
    def too_many_requests(error):
        """Handle 429 Too Many Requests errors"""
        return ResponseService.error(
            message="Too many requests",
            status=429,
            error_code="RATE_LIMIT_EXCEEDED",
            category=ErrorCategory.BUSINESS_LOGIC
        )
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error"""
        return ResponseService.server_error(
            message="Internal server error",
            error_code=ErrorCode.INTERNAL_SERVER_ERROR.value
        )
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all unhandled exceptions"""
        app.logger.error(f"Unhandled exception: {str(error)}")
        return ResponseService.server_error(
            message="An unexpected error occurred",
            error_code=ErrorCode.INTERNAL_SERVER_ERROR.value
        )
    
    # Log DB engine and sanitized URI for diagnostics
    with app.app_context():
        try:
            engine_name = db.engine.name
        except Exception:
            engine_name = 'unknown'
        raw_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        # mask credentials: postgresql://user:pass@host/db -> postgresql://user:***@host/db
        def _sanitize(uri: str) -> str:
            return re.sub(r'(://[^:/@]+):[^@]*@', r'\1:***@', uri)
        app.logger.info('Database engine: %s, uri=%s', engine_name, _sanitize(raw_uri))
    
    # Register blueprints
    from .routes import auth, health, jobs, submit, admin, payment, analytics, staff, diag, export, catalog
    app.register_blueprint(auth.bp)
    app.register_blueprint(health.bp)
    app.register_blueprint(jobs.bp)
    app.register_blueprint(submit.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(payment.bp)
    app.register_blueprint(analytics.bp)
    app.register_blueprint(staff.bp)
    app.register_blueprint(diag.bp)
    app.register_blueprint(export.bp)
    app.register_blueprint(catalog.bp)

    # Initialize seed command
    from . import seed
    seed.init_app(app)
    
    return app