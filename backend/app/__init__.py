from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
from flask_mail import Mail
import os
import re
import logging
import logging.handlers
import json
from datetime import datetime, timezone
import time
from functools import wraps

db = SQLAlchemy(session_options={"expire_on_commit": False})
migrate = Migrate()

# Initialize Redis connection for Flask-Limiter
def get_redis_connection():
    """Get Redis connection for rate limiting"""
    redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379')
    return redis.from_url(redis_url, decode_responses=True)

# Configure Flask-Limiter with Redis backend
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.environ.get('REDIS_URL', 'redis://redis:6379/0')
)
mail = Mail()

# Global monitoring variables
request_count = 0
error_count = 0
performance_metrics = {}

def setup_structured_logging(app):
    """Configure structured logging for the application"""
    if app.debug:
        # Development: Console logging with colors
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        # Production: JSON structured logging
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }
                
                # Add exception info if present
                if record.exc_info:
                    log_entry['exception'] = self.formatException(record.exc_info)
                
                # Add extra fields if present
                if hasattr(record, 'extra_fields'):
                    log_entry.update(record.extra_fields)
                
                return json.dumps(log_entry)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add JSON formatter handler
        json_handler = logging.StreamHandler()
        json_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(json_handler)
        
        # Add file handler for production
        if not app.debug:
            log_dir = os.path.join(app.root_path, '..', 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                os.path.join(log_dir, 'app.log'),
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(JSONFormatter())
            root_logger.addHandler(file_handler)

def setup_performance_monitoring(app):
    """Setup performance monitoring middleware"""
    @app.before_request
    def before_request():
        request.start_time = time.time()
        global request_count
        request_count += 1
    
    @app.after_request
    def after_request(response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log request performance
            extra_fields = {
                'request_id': request_count,
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'user_agent': request.headers.get('User-Agent', ''),
                'ip_address': request.remote_addr
            }
            
            # Log based on performance
            if duration > 1.0:  # Slow requests
                app.logger.warning('Slow request detected', extra={'extra_fields': extra_fields})
            elif response.status_code >= 400:  # Error responses
                global error_count
                error_count += 1
                app.logger.error('Request error', extra={'extra_fields': extra_fields})
            else:
                app.logger.info('Request completed', extra={'extra_fields': extra_fields})
            
            # Update performance metrics
            path = request.path
            if path not in performance_metrics:
                performance_metrics[path] = {
                    'count': 0,
                    'total_duration': 0,
                    'avg_duration': 0,
                    'error_count': 0
                }
            
            metrics = performance_metrics[path]
            metrics['count'] += 1
            metrics['total_duration'] += duration
            metrics['avg_duration'] = metrics['total_duration'] / metrics['count']
            
            if response.status_code >= 400:
                metrics['error_count'] += 1
        
        return response

def setup_error_monitoring(app):
    """Setup comprehensive error monitoring"""
    @app.errorhandler(Exception)
    def handle_exception(error):
        # Log the exception with structured data
        extra_fields = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'request_method': request.method if request else 'N/A',
            'request_path': request.path if request else 'N/A',
            'request_headers': dict(request.headers) if request else {},
            'request_data': request.get_json() if request and request.is_json else None
        }
        
        app.logger.exception('Unhandled exception', extra={'extra_fields': extra_fields})
        
        # Update error metrics
        global error_count
        error_count += 1
        
        # Return standardized error response
        return {
            'error': 'Internal server error',
            'message': 'An unexpected error occurred',
            'error_id': error_count
        }, 500

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
    
    # Rate limiting configuration (env-driven so tests can disable easily)
    ratelimit_enabled_env = os.environ.get('RATELIMIT_ENABLED')
    if ratelimit_enabled_env is not None:
        app.config['RATELIMIT_ENABLED'] = ratelimit_enabled_env.lower() not in ('0', 'false', 'no')
    
    # Setup monitoring and logging
    setup_structured_logging(app)
    setup_performance_monitoring(app)
    setup_error_monitoring(app)
    
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
    def internal_error(error):
        """Handle 500 Internal Server errors"""
        return ResponseService.server_error(
            message="Internal server error",
            error_code=ErrorCode.INTERNAL_ERROR.value
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
    from .routes import auth, health, jobs, submit, admin, payment, analytics, staff, diag, export, catalog, monitoring
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
    app.register_blueprint(monitoring.monitoring_bp)

    # Session-per-request hygiene: remove scoped session after each request
    @app.teardown_request
    def remove_session(exception=None):  # type: ignore[unused-argument]
        try:
            db.session.remove()
        except Exception as e:
            # Sampling-based log to avoid excessive noise under load
            if int(time.time() * 1000) % 100 == 0:
                app.logger.warning('Session teardown remove() failed', extra={
                    'extra_fields': {
                        'error': str(e),
                        'event': 'session_teardown_failure'
                    }
                })

    # Initialize seed command
    from . import seed
    seed.init_app(app)
    
    return app