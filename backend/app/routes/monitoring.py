"""
Monitoring endpoints for comprehensive system monitoring and metrics collection.
Provides health checks, performance metrics, and system status information.
"""

from flask import Blueprint, jsonify, request
from app.services.monitoring_service import monitoring_service
from app.business_logic.shared_services.response_service import ResponseService, ErrorCategory, ErrorCode
import logging

logger = logging.getLogger(__name__)

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/v1/monitoring')

@monitoring_bp.route('/health', methods=['GET'])
def get_health():
    """Get comprehensive system health status"""
    try:
        health_data = monitoring_service.get_comprehensive_health()
        
        # Determine HTTP status code based on health
        if health_data['status'] == 'healthy':
            status_code = 200
        elif health_data['status'] == 'degraded':
            status_code = 200  # Still operational but with issues
        else:
            status_code = 503  # Service unavailable
        
        return jsonify(health_data), status_code
    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        return ResponseService.server_error(
            message="Failed to retrieve health status",
            error_code=ErrorCode.INTERNAL_ERROR.value
        )

@monitoring_bp.route('/metrics/system', methods=['GET'])
def get_system_metrics():
    """Get system-level metrics (CPU, memory, disk, network)"""
    try:
        metrics = monitoring_service.get_system_metrics()
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return ResponseService.server_error(
            message="Failed to retrieve system metrics",
            error_code=ErrorCode.INTERNAL_ERROR.value
        )

@monitoring_bp.route('/metrics/application', methods=['GET'])
def get_application_metrics():
    """Get application-specific metrics (requests, errors, performance)"""
    try:
        metrics = monitoring_service.get_application_metrics()
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Failed to get application metrics: {e}")
        return ResponseService.server_error(
            message="Failed to retrieve application metrics",
            error_code=ErrorCode.INTERNAL_ERROR.value
        )

@monitoring_bp.route('/metrics/database', methods=['GET'])
def get_database_metrics():
    """Get database performance and health metrics"""
    try:
        metrics = monitoring_service.get_database_metrics()
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Failed to get database metrics: {e}")
        return ResponseService.server_error(
            message="Failed to retrieve database metrics",
            error_code=ErrorCode.INTERNAL_ERROR.value
        )

@monitoring_bp.route('/metrics/storage', methods=['GET'])
def get_storage_metrics():
    """Get storage system metrics"""
    try:
        metrics = monitoring_service.get_storage_metrics()
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Failed to get storage metrics: {e}")
        return ResponseService.server_error(
            message="Failed to retrieve storage metrics",
            error_code=ErrorCode.INTERNAL_ERROR.value
        )

@monitoring_bp.route('/metrics/redis', methods=['GET'])
def get_redis_metrics():
    """Get Redis performance and health metrics"""
    try:
        metrics = monitoring_service.get_redis_metrics()
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Failed to get Redis metrics: {e}")
        return ResponseService.server_error(
            message="Failed to retrieve Redis metrics",
            error_code=ErrorCode.INTERNAL_ERROR.value
        )

@monitoring_bp.route('/metrics/all', methods=['GET'])
def get_all_metrics():
    """Get all metrics in a single response"""
    try:
        all_metrics = {
            'timestamp': monitoring_service.get_system_metrics().get('timestamp'),
            'system': monitoring_service.get_system_metrics(),
            'application': monitoring_service.get_application_metrics(),
            'database': monitoring_service.get_database_metrics(),
            'storage': monitoring_service.get_storage_metrics(),
            'redis': monitoring_service.get_redis_metrics()
        }
        return jsonify(all_metrics)
    except Exception as e:
        logger.error(f"Failed to get all metrics: {e}")
        return ResponseService.server_error(
            message="Failed to retrieve metrics",
            error_code=ErrorCode.INTERNAL_ERROR.value
        )

@monitoring_bp.route('/history', methods=['GET'])
def get_metrics_history():
    """Get metrics history for the specified time period"""
    try:
        # Get hours parameter from query string, default to 24 hours
        hours = request.args.get('hours', 24, type=int)
        
        # Validate hours parameter
        if hours < 1 or hours > 168:  # Max 1 week
            return ResponseService.validation_error(
                message="Invalid hours parameter",
                error_code=ErrorCode.INVALID_INPUT.value,
                details={'hours': 'Must be between 1 and 168 hours'}
            )
        
        history = monitoring_service.get_metrics_history(hours)
        return jsonify({
            'hours': hours,
            'count': len(history),
            'data': history
        })
    except Exception as e:
        logger.error(f"Failed to get metrics history: {e}")
        return ResponseService.server_error(
            message="Failed to retrieve metrics history",
            error_code=ErrorCode.INTERNAL_ERROR.value
        )

@monitoring_bp.route('/alerts', methods=['GET'])
def get_performance_alerts():
    """Get current performance alerts"""
    try:
        alerts = monitoring_service.get_performance_alerts()
        return jsonify({
            'timestamp': monitoring_service.get_system_metrics().get('timestamp'),
            'count': len(alerts),
            'alerts': alerts
        })
    except Exception as e:
        logger.error(f"Failed to get performance alerts: {e}")
        return ResponseService.server_error(
            message="Failed to retrieve performance alerts",
            error_code=ErrorCode.INTERNAL_ERROR.value
        )

@monitoring_bp.route('/status', methods=['GET'])
def get_status():
    """Get simplified status for health checks and monitoring"""
    try:
        health_data = monitoring_service.get_comprehensive_health()
        
        # Simplified status response
        status = {
            'status': health_data['status'],
            'timestamp': health_data['timestamp'],
            'uptime_seconds': health_data['uptime_seconds'],
            'components': {}
        }
        
        # Add component statuses
        for component, data in health_data.get('components', {}).items():
            if component == 'system':
                status['components'][component] = 'healthy' if 'error' not in data else 'unhealthy'
            elif component == 'database':
                status['components'][component] = data.get('connectivity', {}).get('status', 'unknown')
            elif component == 'storage':
                status['components'][component] = data.get('status', 'unknown')
            elif component == 'redis':
                status['components'][component] = data.get('connectivity', {}).get('status', 'unknown')
            else:
                status['components'][component] = 'healthy' if 'error' not in data else 'unhealthy'
        
        # Determine HTTP status code
        if status['status'] == 'healthy':
            status_code = 200
        elif status['status'] == 'degraded':
            status_code = 200
        else:
            status_code = 503
        
        return jsonify(status), status_code
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': 'Failed to retrieve status'
        }), 503

@monitoring_bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint for basic connectivity testing"""
    try:
        return jsonify({
            'status': 'ok',
            'timestamp': monitoring_service.get_system_metrics().get('timestamp'),
            'message': 'pong'
        })
    except Exception as e:
        logger.error(f"Ping failed: {e}")
        return jsonify({
            'status': 'error',
            'message': 'ping failed'
        }), 503

@monitoring_bp.route('/info', methods=['GET'])
def get_info():
    """Get system information and configuration"""
    try:
        import os
        import sys
        
        info = {
            'timestamp': monitoring_service.get_system_metrics().get('timestamp'),
            'application': {
                'name': '3D Print Management System',
                'version': '1.0.0',
                'environment': os.environ.get('FLASK_ENV', 'development'),
                'debug': os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
            },
            'system': {
                'python_version': sys.version,
                'platform': sys.platform,
                'architecture': sys.maxsize > 2**32 and '64-bit' or '32-bit'
            },
            'configuration': {
                'database_url_configured': bool(os.environ.get('DATABASE_URL')),
                'redis_url_configured': bool(os.environ.get('REDIS_URL')),
                'mail_configured': bool(os.environ.get('MAIL_USERNAME')),
                'storage_path': os.environ.get('STORAGE_PATH', 'storage')
            }
        }
        
        return jsonify(info)
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        return ResponseService.server_error(
            message="Failed to retrieve system information",
            error_code=ErrorCode.INTERNAL_ERROR.value
        )
