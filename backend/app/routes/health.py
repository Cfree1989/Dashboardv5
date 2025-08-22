from __future__ import annotations
from flask import Blueprint, jsonify, current_app
import os
import psutil
from app import db
from sqlalchemy import text
import redis
from rq import Queue


bp = Blueprint('health', __name__, url_prefix='/api/v1')


def check_database():
    """Check database connectivity and basic operations"""
    try:
        with db.engine.connect() as conn:
            # Basic connectivity test
            conn.execute(text('SELECT 1'))
            
            # Check if we can access the jobs table
            conn.execute(text('SELECT COUNT(*) FROM job LIMIT 1'))
            
        return {'status': 'ok', 'message': 'Database is accessible'}
    except Exception as e:
        return {'status': 'error', 'message': f'Database error: {str(e)}'}


def check_redis():
    """Check Redis connectivity and basic operations"""
    try:
        # Get Redis URL from environment
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        redis_password = os.environ.get('REDIS_PASSWORD')
        
        # Only modify URL if it doesn't already contain authentication
        if redis_password and '@' not in redis_url:
            # Parse Redis URL and add password
            if redis_url.startswith('redis://'):
                redis_url = redis_url.replace('redis://', f'redis://:{redis_password}@')
        
        r = redis.from_url(redis_url)
        r.ping()
        
        # Check if RQ queue is accessible
        queue = Queue(connection=r)
        queue.is_empty()  # This will test the connection
        
        return {'status': 'ok', 'message': 'Redis is accessible'}
    except Exception as e:
        return {'status': 'error', 'message': f'Redis error: {str(e)}'}


def check_storage():
    """Check storage directory accessibility and space"""
    try:
        storage_path = os.environ.get('STORAGE_PATH', 'storage')
        
        # Check if storage directory exists and is writable
        if not os.path.exists(storage_path):
            os.makedirs(storage_path, exist_ok=True)
        
        # Check if directory is writable
        test_file = os.path.join(storage_path, '.health_check_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        
        # Check disk space
        disk_usage = psutil.disk_usage(storage_path)
        usage_percent = (disk_usage.used / disk_usage.total) * 100
        
        if usage_percent > 90:
            return {
                'status': 'warning', 
                'message': f'Storage accessible but disk usage is high: {usage_percent:.1f}%'
            }
        
        return {
            'status': 'ok', 
            'message': f'Storage is accessible, disk usage: {usage_percent:.1f}%'
        }
    except Exception as e:
        return {'status': 'error', 'message': f'Storage error: {str(e)}'}


def check_system_resources():
    """Check system resource usage"""
    try:
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # CPU usage (average over 1 second)
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Disk usage for storage
        storage_path = os.environ.get('STORAGE_PATH', 'storage')
        disk_usage = psutil.disk_usage(storage_path)
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        
        status = 'ok'
        if memory_percent > 90 or cpu_percent > 90 or disk_percent > 90:
            status = 'warning'
        
        return {
            'status': status,
            'message': 'System resources monitored',
            'details': {
                'memory_percent': memory_percent,
                'cpu_percent': cpu_percent,
                'disk_percent': disk_percent
            }
        }
    except Exception as e:
        return {'status': 'error', 'message': f'Resource check error: {str(e)}'}


@bp.route('/health', methods=['GET'])
def api_health():
    """Comprehensive health check endpoint"""
    components = {
        'database': check_database(),
        'redis': check_redis(),
        'storage': check_storage(),
        'system': check_system_resources()
    }
    
    # Determine overall status
    status = 'ok'
    for component_name, component_status in components.items():
        if component_status['status'] == 'error':
            status = 'error'
            break
        elif component_status['status'] == 'warning' and status == 'ok':
            status = 'warning'
    
    payload = {
        'status': status,
        'components': components,
        'env': 'testing' if current_app.config.get('TESTING') else 'production-like',
        'timestamp': current_app.config.get('START_TIME', 'unknown')
    }
    
    http_code = 200 if status == 'ok' else (503 if status == 'error' else 200)
    return jsonify(payload), http_code


@bp.route('/health/db', methods=['GET'])
def health_db():
    """Database-specific health check"""
    result = check_database()
    http_code = 200 if result['status'] == 'ok' else 503
    return jsonify(result), http_code


@bp.route('/health/redis', methods=['GET'])
def health_redis():
    """Redis-specific health check"""
    result = check_redis()
    http_code = 200 if result['status'] == 'ok' else 503
    return jsonify(result), http_code


@bp.route('/health/storage', methods=['GET'])
def health_storage():
    """Storage-specific health check"""
    result = check_storage()
    http_code = 200 if result['status'] == 'ok' else 503
    return jsonify(result), http_code


@bp.route('/health/system', methods=['GET'])
def health_system():
    """System resources health check"""
    result = check_system_resources()
    http_code = 200 if result['status'] == 'ok' else 503
    return jsonify(result), http_code


