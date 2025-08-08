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
    from .routes import auth, jobs, submit, payment, analytics, staff, diag, admin
    app.register_blueprint(auth.bp)
    app.register_blueprint(jobs.bp)
    app.register_blueprint(submit.bp)
    app.register_blueprint(payment.bp)
    app.register_blueprint(analytics.bp)
    app.register_blueprint(staff.bp)
    app.register_blueprint(diag.bp)
    app.register_blueprint(admin.bp)

    # Initialize seed command
    from . import seed
    seed.init_app(app)
    
    return app